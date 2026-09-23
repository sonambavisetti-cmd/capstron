# Implementation Plan

## Summary
This implementation plan decomposes the approved architecture (FastAPI backend, React frontend, async PDF worker, Redis queue, Postgres, S3 storage, Stripe adapter) into an ordered set of development tasks for an MVP. Each task maps to specific files under dev/, frontend/, test-automation/, or infra/, references the functional/non-functional requirements it satisfies (see requirements.md), lists dependencies, a person-day estimate, a suggested owner role, acceptance criteria and test types. The plan prioritizes transactional order creation with inventory reservation, secure admin access, deterministic PDF invoice generation (ReportLab), and CI checks that prevent secrets in source control.

## Task Breakdown

### TASK-01: Repo skeleton, CI & developer environment
- Description: Create the repository layout and minimal starter files for services, frontend and tests; add base GitHub Actions workflow, .gitignore, and `.env.example`.
- Target files: `dev/app/main.py`, `dev/__init__.py`, `frontend/package.json`, `test-automation/package.json`, `requirements.txt`, `.env.example`, `.gitignore`, `.github/workflows/ci.yml`
- Depends on: none
- Satisfies: FR-01 (homepage present), FR-02 (catalog scaffold), NFR-05 (no secrets in repo)
- Time estimate: 1.5 person-days
- Owner: devops/backend
- Acceptance criteria / DoD: repository contains the top-level folders (dev/, frontend/, test-automation/, infra/), CI job scaffold exists and runs a placeholder job, `.env.example` present and `.env` listed in `.gitignore`.
- Test types: none (smoke CI job runs)

### TASK-02: Configuration loader & secrets enforcement
- Description: Implement environment-based configuration, a secrets scanning CI job, and developer pre-commit hook template. Document secret handling and required environment variables.
- Target files: `dev/config.py`, `scripts/secret_scan.sh`, `dev/docs/secrets.md`, `.github/workflows/secret-scan.yml`
- Depends on: TASK-01
- Satisfies: FR-09, NFR-05
- Time estimate: 0.5 person-days
- Owner: backend/devops
- Acceptance criteria / DoD: config loader reads env vars and raises descriptive errors for missing required vars; CI job fails on detected secrets; `.env.example` documents required variables.
- Test types: unit tests for config parsing; CI secret-scan

### TASK-03: Local infra (dev) - Postgres, Redis, MinIO
- Description: Provide a local docker-compose for Postgres, Redis, MinIO (S3-compatible) used for local dev and CI disposable containers; include scripts to bring up/down the stack.
- Target files: `infra/docker-compose.dev.yml`, `infra/README.md`, `infra/scripts/start_dev_stack.sh`
- Depends on: TASK-01, TASK-02
- Satisfies: NFR-05, NFR-04 (enables load testing in dev), NFR-01 (local responsive testing)
- Time estimate: 1.0 person-days
- Owner: devops
- Acceptance criteria / DoD: developers can run a single script to start Postgres, Redis, MinIO; CI jobs can instantiate disposable Postgres container for migration validation.
- Test types: integration test against disposable DB

### TASK-04: Data models & Alembic migrations
- Description: Define SQLAlchemy models (Product, SiteSettings, Customer, Order, OrderItem, Invoice, AdminUser), DB connectivity wrapper and Alembic migration scripts.
- Target files: `dev/app/models.py`, `dev/app/db.py`, `alembic/env.py`, `alembic/versions/0001_initial.py`
- Depends on: TASK-02, TASK-03
- Satisfies: FR-02, FR-06, FR-07
- Time estimate: 4.0 person-days
- Owner: backend
- Acceptance criteria / DoD: models implement fields listed in architecture.md; alembic migration applies cleanly against disposable Postgres; unit tests validate model constraints and basic CRUD.
- Test types: unit tests, migration validation (CI)

### TASK-05: Storage adapters (local and S3)
- Description: Implement a pluggable storage adapter used by the API and worker to store logos and generated PDFs. Local adapter for dev (filesystem/MinIO); S3 adapter for prod with signed URL generation.
- Target files: `dev/app/storage/adapter.py`, `dev/app/storage/local.py`, `dev/app/storage/s3.py`
- Depends on: TASK-03, TASK-02
- Satisfies: FR-07, NFR-05
- Time estimate: 1.0 person-day
- Owner: backend
- Acceptance criteria / DoD: configuration switches between local and S3 adapter; signed URLs generated for stored objects; unit tests for adapter behavior.
- Test types: unit, integration (with MinIO)

### TASK-06: Backend API skeleton & product endpoints
- Description: FastAPI application skeleton, routing, OpenAPI docs and product endpoints (GET /api/products, GET /api/products/:id) with small caching layer (Redis TTL) and image URL handling.
- Target files: `dev/app/main.py`, `dev/app/api/products.py`, `dev/app/schemas/product.py`, `dev/app/api/__init__.py`
- Depends on: TASK-04, TASK-03, TASK-05
- Satisfies: FR-01, FR-02, NFR-04
- Time estimate: 2.0 person-days
- Owner: backend
- Acceptance criteria / DoD: endpoints return product list/detail with fields required by FR-02; responses include cache-control and optional ETag; unit + integration tests validate behavior and response format.
- Test types: unit, integration

### TASK-07: Cart, checkout API, validation & idempotency
- Description: Implement cart representation (server-side optional), POST /api/orders that validates input (Pydantic), calculates totals, reserves inventory via Redis reservation tokens with TTL and records Idempotency-Key handling (Redis/DB), and persists a pending order.
- Target files: `dev/app/api/cart.py`, `dev/app/api/orders.py`, `dev/app/validation.py`, `dev/app/services/inventory.py`, `dev/app/services/idempotency.py`
- Depends on: TASK-04, TASK-06, TASK-03, TASK-02
- Satisfies: FR-03, FR-04, FR-05, FR-06, NFR-03
- Time estimate: 4.0 person-days
- Owner: backend
- Acceptance criteria / DoD: valid order payloads create a pending order and return order_reference; invalid payloads return clear validation errors (FR-05); Idempotency-Key for duplicate POST returns same order_reference and does not create duplicates; reservation TTL behavior covered by unit/integration tests.
- Test types: unit, integration, concurrency tests

### TASK-08: Payment adapter & webhook handling
- Description: Implement payment adapter interface and Stripe test-mode adapter, POST /api/payments/create-session, POST /api/payments/webhook handler that verifies signatures and updates order/payment status transactionally; ensure idempotency on payment creation.
- Target files: `dev/app/payments/interface.py`, `dev/app/payments/stripe_adapter.py`, `dev/app/api/payments.py`, `dev/app/services/payment_service.py`
- Depends on: TASK-07, TASK-02
- Satisfies: FR-04, FR-06, ADR-04
- Time estimate: 2.0 person-days
- Owner: backend
- Acceptance criteria / DoD: payment session creation uses Idempotency-Key; webhook handler verifies signature and marks order paid then enqueues invoice generation; unit and integration tests simulate Stripe test events (local fixtures).
- Test types: unit, integration, webhook E2E (Playwright can simulate flow where feasible)

### TASK-09: Order finalization & inventory decrement logic
- Description: Implement the final transactional path that finalizes an order (on successful payment or COD) and decrements product quantity using SELECT ... FOR UPDATE with retry and fallback when Redis reservations are missing.
- Target files: `dev/app/services/order_service.py`, `dev/app/services/transactional.py`
- Depends on: TASK-07, TASK-08, TASK-04
- Satisfies: FR-06, NFR-06
- Time estimate: 2.5 person-days
- Owner: backend
- Acceptance criteria / DoD: finalization path is atomic and prevents double-selling under concurrent requests; integration/concurrency tests (simulated concurrent checkout) show no negative inventory state.
- Test types: integration, load/concurrency test

### TASK-10: Background worker & deterministic PDF invoice generation
- Description: Implement an RQ worker to generate invoice PDFs using ReportLab and the SiteSettings record; store the PDF using storage adapter and update Invoice.status (pending -> ready|failed). Expose GET /api/orders/:id/invoice returning metadata and signed URL when ready.
- Target files: `dev/app/workers/invoice_worker.py`, `dev/app/services/invoice.py`, `dev/app/pdf/reportlab_invoice.py`, `dev/app/api/invoices.py`
- Depends on: TASK-05, TASK-09, TASK-04
- Satisfies: FR-07, NFR-02
- Time estimate: 3.5 person-days
- Owner: backend
- Acceptance criteria / DoD: invoices generated contain invoice number, date, customer details, itemized list, totals and company details; PDF stored and a signed URL returned only when Invoice.status == ready; unit tests for PDF content metadata and an integration test that runs worker end-to-end.
- Test types: unit, integration, E2E (Playwright verifies download in a flow)

### TASK-11: Admin authentication & admin endpoints
- Description: Implement admin login (server-side sessions stored in Redis) with Argon2 password hashing, rate limiting on login, endpoints for listing orders, viewing order details and marking orders as processed.
- Target files: `dev/app/api/admin.py`, `dev/app/auth.py`, `dev/app/scripts/seed_admin.py`, `dev/app/schemas/admin.py`
- Depends on: TASK-02, TASK-04
- Satisfies: FR-08, NFR-03
- Time estimate: 2.0 person-days
- Owner: backend
- Acceptance criteria / DoD: admin endpoints require authenticated session; successful login sets Secure HttpOnly cookie; permission checks prevent non-admin access; tests validate lockout/rate-limit behavior.
- Test types: unit, integration, E2E (Playwright admin flow)

### TASK-12: Frontend - Customer storefront pages
- Description: Implement React (Vite) storefront pages: Homepage, ProductList, ProductDetail, Cart, Checkout, OrderConfirmation. Use Tailwind/CSS for responsive layout and polling for invoice readiness.
- Target files: `frontend/src/pages/Home.jsx`, `frontend/src/pages/ProductList.jsx`, `frontend/src/pages/ProductDetail.jsx`, `frontend/src/pages/Cart.jsx`, `frontend/src/pages/Checkout.jsx`, `frontend/src/pages/Confirmation.jsx`, `frontend/src/App.jsx`
- Depends on: TASK-06, TASK-10, TASK-05
- Satisfies: FR-01, FR-02, FR-03, FR-04, NFR-01
- Time estimate: 6.0 person-days
- Owner: frontend
- Acceptance criteria / DoD: pages render required fields and are responsive at common breakpoints; checkout calls backend APIs and handles validation errors; invoice download button appears when invoice is ready. Manual UAT verifies NFR-01.
- Test types: unit (components), E2E (Playwright)

### TASK-13: Frontend - Admin UI
- Description: Implement a small admin SPA under `/admin` to list orders, view details, and mark processed (protected route). Server-side sessions used for auth.
- Target files: `frontend/src/pages/admin/Orders.jsx`, `frontend/src/pages/admin/OrderView.jsx`, `frontend/src/pages/admin/Login.jsx`
- Depends on: TASK-11, TASK-04
- Satisfies: FR-08, NFR-03
- Time estimate: 2.5 person-days
- Owner: frontend
- Acceptance criteria / DoD: admin UI requires login and can list and update orders; tests cover role enforcement.
- Test types: E2E (Playwright), unit

### TASK-14: Tests — pytest unit & integration coverage
- Description: Implement pytest suite covering models, services, API endpoints, idempotency and concurrency scenarios. Use fixtures for disposable Postgres, Redis and MinIO.
- Target files: `dev/tests/test_models.py`, `dev/tests/test_orders.py`, `dev/tests/test_payments.py`, `dev/tests/concurrency/test_inventory_race.py`
- Depends on: TASK-04, TASK-06, TASK-07, TASK-09
- Satisfies: FR acceptance criteria (FR-01..FR-09), NFR-02
- Time estimate: 3.0 person-days
- Owner: test/backend
- Acceptance criteria / DoD: pytest coverage for critical paths (order creation, payment webhook, invoice enqueue, inventory race) runs in CI; migration validation job passes.
- Test types: unit, integration, concurrency

### TASK-15: Tests — Playwright E2E flows
- Description: Implement Playwright TypeScript E2E tests for end-to-end scenarios: browse -> add to cart -> checkout (COD), browse -> checkout (ONLINE simulated with Stripe test session), order confirmation, invoice download, admin marking processed.
- Target files: `test-automation/playwright.config.ts`, `test-automation/e2e/checkout.spec.ts`, `test-automation/e2e/admin.spec.ts`
- Depends on: TASK-12, TASK-13, TASK-10
- Satisfies: FR acceptance criteria (FR-01..FR-09), NFR-02, NFR-01
- Time estimate: 3.5 person-days
- Owner: test/frontend
- Acceptance criteria / DoD: Playwright tests run in CI against a staging stack; they assert presence of required invoice fields in downloaded PDF metadata and admin workflow.
- Test types: E2E

### TASK-16: Load & inventory concurrency stress tests
- Description: Author load test scripts (k6 or locust) to validate p95 product-list latency < 500ms and inventory reservation behavior under contention.
- Target files: `test-automation/load/k6/product_list_test.js`, `test-automation/load/locust/inventory_stress.py`, `dev/tests/concurrency/report.md`
- Depends on: TASK-06, TASK-07, TASK-03
- Satisfies: NFR-04, architecture load & concurrency requirements
- Time estimate: 2.0 person-days
- Owner: test/devops
- Acceptance criteria / DoD: load test results demonstrating p95 < 500ms for product-list under targeted concurrency and inventory stress report included in Phase 4 artifacts.
- Test types: load / concurrency tests

### TASK-17: CI pipeline finalization & PR checks
- Description: Add and wire CI jobs: lint (black/isort/flint), static typing (mypy), unit tests (pytest), migrations validation (Alembic against disposable Postgres), Playwright (E2E), secret scanning, and containerized test database orchestration.
- Target files: `.github/workflows/ci.yml`, `.github/workflows/playwright.yml`, `scripts/ci_runner.sh`
- Depends on: TASK-01, TASK-12, TASK-14, TASK-15
- Satisfies: NFR-05, NFR-11
- Time estimate: 1.5 person-days
- Owner: devops
- Acceptance criteria / DoD: PRs must pass all CI jobs before merge; migrations validated against disposable Postgres; secret scanning included.
- Test types: CI validation jobs

### TASK-18: Infra IaC for staging/prod & runbooks
- Description: Provide Terraform or cloud-provider templates for Postgres (managed), Redis, S3 bucket, and instructions for wiring secrets (Secrets Manager/GitHub Actions secrets). Include deployment runbook for staging.
- Target files: `infra/terraform/main.tf`, `infra/README.md`, `dev/ops/deploy_runbook.md`
- Depends on: TASK-03, TASK-17
- Satisfies: NFR-05, DR-03
- Time estimate: 2.5 person-days
- Owner: devops
- Acceptance criteria / DoD: IaC templates include resources for Postgres, Redis, S3 (or place-holder modules) and runbook documents steps to provision resources and rotate secrets.
- Test types: manual verification, IaC plan validation

### TASK-19: Observability & health checks
- Description: Add basic health endpoints, structured logging, and metrics for inventory reservations, queue depth and invoice job failures.
- Target files: `dev/app/monitoring.py`, `dev/app/logging_config.py`, `dev/app/metrics.py`
- Depends on: TASK-06, TASK-11, TASK-10
- Satisfies: NFR-04, NFR-02
- Time estimate: 1.0 person-day
- Owner: backend/devops
- Acceptance criteria / DoD: /healthz endpoint present; basic metrics exported for queue depth and job failures; logs include redaction of sensitive fields.
- Test types: unit, integration checks

### TASK-20: Documentation, backup & retention runbooks
- Description: Author runbooks for backups, migrations, restore drills, rotation of secrets and instructions for local developer onboarding.
- Target files: `dev/ops/backup.md`, `dev/ops/migration.md`, `dev/docs/onboarding.md`
- Depends on: TASK-04, TASK-18
- Satisfies: NFR-05
- Time estimate: 1.0 person-day
- Owner: tech-lead/devops
- Acceptance criteria / DoD: runbooks reviewed and tested in a restore drill; onboarding doc enables a new developer to run full stack locally.

### Execution Order & Time Summary
- Execution order follows dependencies above (TASK-01 -> TASK-20). Total estimated effort (MVP): 47.0 person-days.

### PR Checklist (high-level)
- Run unit tests and ensure CI green
- Run linters/formatters and type-checks
- Validate Alembic migrations against disposable Postgres
- Run Playwright E2E (staging) for checkout/invoice flows
- Run secret-scan job
- Ensure no secrets in PR and update documentation if config changes

### Required infra & external resources
- Stripe test account (for TASK-08)
- S3 bucket or MinIO (TASK-05)
- Redis instance (TASK-03)
- PostgreSQL instance (TASK-03)
- GitHub Actions secrets / Secrets Manager (TASK-02, TASK-18)

### Risk Register (abridged)
- Secrets committed: medium/ high — mitigate via secret-scan and pre-commit hooks
- Inventory race: high/ high — mitigate via reservation + SELECT FOR UPDATE + concurrency tests
- PDF fidelity: medium/ medium — manual UAT and iterate on ReportLab template

Co-authored-by: Lead Engineer <lead@vinayaka.example.com>## Execution Order
1. TASK-01
2. TASK-02
3. TASK-03
4. TASK-04
5. TASK-05
6. TASK-06
7. TASK-07
8. TASK-08
9. TASK-09
10. TASK-10
11. TASK-11
12. TASK-12
13. TASK-13
14. TASK-14

## Risk Register
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Secrets leaked | Medium | High | CI secret-scan, .env ignored, use secret manager in prod |
| Invoice generation blocks checkout | Medium | High | Use async worker + queue; inline only with strict timeout |
| Inventory race conditions | High | High | Transactional locks, optimistic retries, concurrency tests |
| Local FS in multi-instance | High | Medium | S3 adapter in prod, signed URLs, migration doc |
| Payment provider outage | Medium | High | Idempotency, queue pending payments, fallback provider |

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
