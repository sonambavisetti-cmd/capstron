# Architecture

## Overview

Vinayaka File Works storefront: a lightweight web application that enables customers to browse products, add items to a cart, complete checkout (Cash on Delivery or Online payment), and download PDF invoices matching the provided sample. Staff can review orders and mark them as processed via a protected admin interface.

This document defines a minimal-yet-production-ready architecture that follows repository constraints: Python server code lives in dev/, Playwright TypeScript tests live in test-automation/, and frontend code (React) is colocated in frontend/ (or built as a static artifact). The design addresses prior design-review feedback by specifying admin authentication, secrets handling, an asynchronous invoice lifecycle, database concurrency controls, backups/encryption, and test alignment.

## Component Diagram (ASCII / Mermaid)

```mermaid
flowchart LR
  Browser[Browser (Customer)] -->|HTTPS| Frontend[React SPA - storefront]
  Browser -->|HTTPS| AdminUI[React SPA - admin]
  Frontend -->|HTTPS REST| API[Backend API - FastAPI]
  AdminUI -->|HTTPS REST| API
  API -->|SQL| DB[(Postgres)]
  API -->|enqueue job| Queue[(Redis + RQ)]
  Queue -->|worker| Worker[Background Worker]
  Worker -->|generate| PDF[ReportLab PDF generator]
  Worker -->|store| ObjectStore[(S3 / MinIO)]
  API -->|webhook / REST| Payment[Payment Provider (Stripe)]
  API -->|auth/session| Auth[Session Store (Redis)]
  API -->|logs/metrics| Observability[Logging & Monitoring]
```

Data flow & Order lifecycle summary:

Customer -> Frontend -> POST /api/orders -> Backend API

1. API validates the request and attempts a short-lived inventory reservation (see Inventory Reservation below). API creates an Order record in the DB with status "pending" and payment_status "pending" inside a transaction. The creation is tied to an Idempotency-Key header (see Idempotency section) to avoid duplicate orders from retries.

2. For ONLINE payments: API creates a payment session with the payment provider (Stripe adapter) and returns the session info to the frontend. The final order confirmation only occurs after the payment provider notifies the system (webhook) that the payment succeeded. The webhook handler verifies the provider signature, updates payment_status to "paid" and order_status to "confirmed" (transactionally), and then enqueues final invoice PDF generation (worker).

3. For Cash on Delivery (COD): after the order is persisted and basic validation completes, the API marks the order_status as "confirmed" and enqueues final invoice generation immediately (or at admin confirmation if business requires).

4. Invoice generation: Workers generate the final invoice PDF only when the order is in a final/confirmed state (paid for ONLINE flows or confirmed for COD). Worker stores the PDF in object storage and updates the Invoice record: status transitions from pending -> ready|failed. Frontend may poll GET /api/orders/:id/invoice or GET /api/orders/:id to determine invoice readiness and fetch a signed URL to download the PDF when ready.

Idempotency (Order/Payment):
- Require an Idempotency-Key header on POST /api/orders and on payment creation endpoints. The backend persists the Idempotency-Key (Redis or DB) with a TTL (24 hours) mapping to the canonical order_reference and returned response. Repeated requests with the same key return the original order response rather than creating duplicates.

Inventory Reservation (locking algorithm):
- Primary strategy: attempt a fast reservation using Redis (reserve a quantity token per product) with a reservation TTL of 10 minutes. Reservation flow:
  - On POST /api/orders: reserve desired quantities in Redis (atomic decrement of available reservation tokens). If the reservation succeeds, create DB Order in 'pending' state without decrementing the authoritative "available_quantity" yet.
  - Start payment flow (ONLINE) or mark confirmed (COD). If payment succeeds within reservation TTL, finalize the order in a DB transaction that decrements available_quantity (SELECT ... FOR UPDATE) and sets order_status to confirmed.
  - If reservation TTL expires before confirmation, reservation is released and the order must be marked expired / failed; the customer must retry.
- Fallback: if Redis is unavailable, use a DB transactional approach with SELECT ... FOR UPDATE to lock product rows and verify/decrement stock within the same transaction before creating the confirmed order. Documented fallbacks ensure no double-selling.
- Monitoring: capture reservation TTL expirations, reservation failures, and lock contention metrics; add stress tests to validate behavior under concurrent checkout.

Product-list caching & performance plan:
- Use Redis short TTL cache for GET /api/products (recommended TTL 30s) with cache busting on product updates. Serve images via CDN (CloudFront) or S3 presigned URLs cached by CDN.
- Invalidation: on product updates, publish an event (Pub/Sub or Redis pub/sub) to invalidate relevant cache keys or increment a version token used in cache keys.
- Load testing: define a k6 or locust scenario that simulates realistic browse+checkout traffic. Acceptance criterion: p95 product-list latency < 500ms under expected concurrency (define expected concurrent users in project plan). Attach a load test report as part of Phase 3 deliverables.

SiteSettings / CompanyProfile (authoritative content):
- Add a SiteSettings table (company_name, address_lines, phone, logo_s3_key, invoice_footer_template) used by the frontend and PDF generator to ensure consistent company details across homepage and invoices.

CI / Secrets enforcement:
- Add `.env` to `.gitignore` and configure a CI job that runs a secret scanner (e.g., detect-secrets or GitHub CodeQL secret scanning) as part of PR checks. The job should fail if secrets are detected. Document this in the CI/CD section and add a pre-commit hook template for local scanning.

Load & concurrency artifacts (required for Phase 4):
- Provide a product-list load test report (k6/locust) demonstrating p95 < 500ms.
- Provide an inventory concurrency stress test (script + results) showing acceptable levels of reservation success and low double-sell probability.

Frontend polling behaviour:
- Frontend should poll invoice status with exponential backoff or subscribe to a websocket/notification if available. Do not display a signed invoice URL until Invoice.status == ready.



## Components

| Component | Responsibility | Technology |
|-----------|---------------|------------|
| Frontend (Customer) | Homepage, product listing, cart, checkout, order confirmation, invoice download | React (Vite), React Router, Tailwind (or CSS)
| Admin UI | Order list, view order, mark processed, admin login | React (same codebase or small static app served under /admin)
| Backend API | Validation, order persistence, payment orchestration, invoice endpoints, admin endpoints | FastAPI, Pydantic, SQLAlchemy
| Database | Transactional data: products, orders, invoices, admin users | PostgreSQL (prod), SQLite (dev)
| Background Worker | Asynchronous PDF generation, webhook processing, retries/DLQ | RQ (Redis) or Celery
| PDF Generation | Render invoice PDFs matching sample, deterministic server-side templates | ReportLab (Python) — ADR documented
| Object Storage | Store generated PDFs and uploaded assets; serve via signed URLs | AWS S3 (prod), MinIO/local (dev)
| Payment Integration | Create payment sessions, process webhooks, verify signatures | Stripe (recommended) via adapter pattern
| Auth/Session Store | Admin session storage, rate-limiting backstop | Redis (sessions, rate limiting counters)
| CI/CD & Tests | Unit tests, migrations check, Playwright E2E in TypeScript | GitHub Actions, pytest (dev/), Playwright TS (test-automation/)
| Observability | Logs, metrics, health checks, alerts | CloudWatch/Datadog or equivalent

Enforcement: All Python server code must live in dev/; Playwright TypeScript code must live in test-automation/. This avoids cross-language test placement issues flagged in the design review.

## Data Model (summary)

- Product: id, sku, name, description, unit_price_cents, image_url, quantity_available, timestamps
- Customer: id, name, phone, email, address fields, timestamps
- Order: id, order_reference, customer_id, total_amount_cents, payment_method, payment_status, order_status, timestamps
- OrderItem: id, order_id, product_id, sku, name, unit_price_cents, quantity, line_total_cents
- Invoice: id, order_id, invoice_number, invoice_date, pdf_path (S3 key), status (pending|ready|failed), created_at
- AdminUser: id, username, password_hash, role, mfa_enabled, created_at

Key constraints:
- Order creation and inventory decrement are performed in a single DB transaction with row-level locking (SELECT ... FOR UPDATE) to prevent double-selling.
- OrderItem stores denormalized product name/price to retain historical accuracy.

## API Surface (high-level)

| Endpoint / Event | Method | Purpose / Consumer |
|------------------|--------|--------------------|
| GET /api/products | GET | Product list (frontend)
| GET /api/products/:id | GET | Product detail
| POST /api/cart | POST | Optional persisted cart
| POST /api/orders | POST | Submit checkout (frontend) — returns order_reference and order status
| GET /api/orders/:id | GET | Order detail (frontend / admin)
| GET /api/orders/:id/invoice | GET | Invoice metadata (status) or redirect to signed S3 URL
| GET /api/orders/:id/invoice/download | GET | (Optional) proxy download endpoint returning PDF stream
| PUT /api/orders/:id/status | PUT | Admin — update status (mark processed)
| POST /api/payments/create-session | POST | Start online payment (frontend)
| POST /api/payments/webhook | POST | Payment provider webhook (verify signature)
| POST /api/admin/login | POST | Admin login — server sets secure HttpOnly session cookie
| POST /api/admin/logout | POST | Destroy admin session

Notes:
- POST /api/orders enqueues async work for PDF generation. APIs return structured error objects and use consistent HTTP status codes.
- Webhook endpoints validate provider signatures, and payment POSTs require Idempotency-Key handling (stored in Redis for 24h).

## Technology Stack (summary & rationale)

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | React + Vite, Tailwind | Fast iteration, familiar ecosystem, static hosting options
| Backend | FastAPI (Python), Pydantic, SQLAlchemy | Fast development, clear validation, Python ecosystem for PDF
| DB | PostgreSQL (RDS / managed) | ACID for order/inventory; reliable for transactional workloads
| Migrations | Alembic | Standard Python migration tool; CI validation
| PDF | ReportLab (server-side) | Pure-Python, minimal system deps (see ADR)
| Queue | Redis + RQ (or Celery if needed) | Lightweight async processing and retries
| Object Storage | S3 (prod), MinIO (dev) | Durable, multi-instance friendly
| Auth | Server-side sessions (Redis) + optional JWT adapters | Sessions simplify admin flows and CSRF protection
| Payment | Stripe adapter (test mode) | Strong sandbox and webhooks; adapter keeps provider pluggable
| Tests | pytest (dev/), Playwright TypeScript (test-automation/) | Aligns with SDLC constraints
| CI/CD | GitHub Actions | CI runs migrations check, unit tests, and Playwright E2E in separate jobs

## Security Considerations (detailed)
- Secrets: do not commit .env. Add `.env` to `.gitignore`. Use AWS Secrets Manager / GitHub Actions secrets / Vault for production secrets. Enforce secret scanning in CI and pre-commit hooks.
- Transport: TLS 1.2+ (prefer TLS 1.3) everywhere; HSTS enabled in production.
- Auth: Argon2id for password hashing (recommended starter params documented and tuned to infra). Admin sessions stored server-side in Redis; cookies set with HttpOnly and Secure. Account lockout after 5 failures; rate-limit login endpoints per IP and per account. Optional TOTP-based MFA.
- Payment: Use provider tokenization; never handle raw card data. Require Idempotency-Key for payment creation. Validate webhooks by signature.
- Input validation & DB safety: Pydantic for request validation and SQLAlchemy with parameterized queries. Order/inventory modifications wrapped in DB transactions and row locks.
- Least privilege: DB credentials with minimal privileges; S3 buckets with restricted access; signed URLs for downloads.
- Logging & auditing: immutable logs for payments and order state transitions. Redact sensitive PII from general logs.

## Scalability & Reliability
- Stateless API instances behind LB, autoscaled. Sessions in Redis and DB as single source-of-truth.
- Background workers scale horizontally; queue depth monitored and worker counts adjusted automatically.
- Database: managed Postgres with periodic backups (daily), PITR enabled; snapshots retained 30 days; cross-region weekly copy retained 90 days. Restore drills quarterly.
- CDN for static assets and signed S3 URLs for PDFs to minimize backend bandwidth.
- Monitoring: request latency, error rate, queue depths, worker failures, payment failure rates. Alerts for service degradation.
- Cache: short TTL Redis cache for product list (invalidate on updates) to help satisfy product-list latency SLA.

## Migration & Deployment Notes
- Local dev: SQLite & local filesystem or MinIO; `.env` for local config (not committed).
- CI: run Alembic migrations against a disposable Postgres container to validate migrations. Run unit tests (dev/) and Playwright tests (test-automation/) in separate CI jobs.
- Production: managed Postgres (RDS/Azure Database), S3, Redis (managed), deployed services to container platform or PaaS (Render/Heroku/Fly) with environment variables injected from secret manager.

## ADRs

### ADR-01: Monorepo vs multiple repositories
- **Status**: Accepted
- **Context**: Project is small scope and team size is small. The SDLC enforces Python code in dev/ and Playwright tests in test-automation/.
- **Decision**: Use a monorepo with clear folder boundaries (dev/, frontend/, test-automation/, infra/). This simplifies CI and cross-cutting changes.
- **Consequences**: Easier coordination, single CI pipeline; requires disciplined ownership and folder-level CI jobs.

### ADR-02: PDF Generation strategy (ReportLab, async workers)
- **Status**: Accepted
- **Context**: PDF must be reliable and consistent; server-side generation simplifies access control and storage.
- **Decision**: Use ReportLab for deterministic PDF generation executed by background workers. Store PDFs in object storage and serve signed URLs. Keep option to revisit HTML->PDF if styling requires WYSIWYG.
- **Consequences**: Minimal system dependencies and simpler containers; more manual layout coding; possible re-work if exact CSS-based rendering is required.

### ADR-03: Database & migration tooling (Postgres + Alembic)
- **Status**: Accepted
- **Context**: Need ACID guarantees for order/inventory and repeatable migrations.
- **Decision**: Postgres for production; Alembic for migration management; CI runs migrations against a disposable Postgres DB to validate migrations.
- **Consequences**: Strong transactional guarantees; adds CI complexity and requires migration discipline.

### ADR-04: Payment approach (Pluggable adapter; Stripe recommended)
- **Status**: Accepted
- **Context**: Provider choice affects PCI scope and region support.
- **Decision**: Implement a payment adapter interface and use Stripe in test mode for MVP. Require Idempotency-Key and webhook signature verification.
- **Consequences**: Faster integration and QA using Stripe sandbox; retains ability to swap providers.

## Risks and Open Questions
- Payment provider for production (business decision): Stripe recommended; confirm acceptance for local market and fees.
- Authoritative company contact/address for invoice: required to finalize invoice footer.
- PDF styling fidelity: if pixel-perfect rendering is required, may need to migrate to HTML->PDF tooling (headless Chromium).
- Data retention vs legal/financial retention: clarify with legal how long invoices and PII must be retained; record retention policy in infra docs.
- Admin provisioning and rotation: define onboarding steps and secrets rotation cadence (recommend 90 days).
- Inventory concurrency at high load: heavy parallel checkout traffic must be load-tested; consider optimistic locking or additional business rules if contention is high.

---

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
