# VNK-2 — Implementation Plan (Planning)

## Objective
Implement the **human-approved** enhancements for Jira key **VNK-2**:
1) **Quote/Enquiry end-to-end**: ensure the quote enquiry API is registered in the Flask app and that quote enquiries can be submitted and persisted reliably.
2) **Persistent, validated cart**: replace the in-memory cart with a **DB-backed** cart with validation and CRUD-style endpoints suitable for multi-worker deployments.

This PR contains **planning artifacts only** (no application code changes).

---

## Scope
### In scope (approved)
- **VNK-2-ENH-001** (Quote enquiry end-to-end)
  - Register `quote_requests` blueprint so API endpoints are reachable.
  - Ensure POST endpoint persists `QuoteEnquiry` and returns confirmation.
  - (As already present) accept JSON and form submissions.

- **VNK-2-ENH-002** (Persistent, validated cart)
  - Introduce SQLAlchemy models + constraints for `Cart` and `CartItem`.
  - Add Alembic migration(s) to create cart tables.
  - Implement validated cart endpoints: **add / update / remove / get**.
  - Preserve existing routes for backward compatibility.

### Out of scope (explicitly not approved)
- GST/currency changes, invoice numbering, order workflow/idempotency, expanded order details, PDF invoice generation, catalog filters, and broader test expansion.

---

## Approved Jira Requirements (Traceability)
Approved enhancements and Jira requirements supplied by workflow context:

- **VNK-2-ENH-001**
  - Epic: **VNK-39** — Quote enquiries (end-to-end API wiring & persistence)
  - Story: **VNK-40** — Wire quote enquiry API endpoint and persist QuoteEnquiry
  - Task: **VNK-41** — Register quote_requests blueprint in app startup
  - Task: **VNK-42** — Implement quote enquiry POST validation & persistence

- **VNK-2-ENH-002**
  - Epic: **VNK-43** — Persistent, validated shopping cart (DB-backed cart APIs)
  - Story: **VNK-44** — Create DB-backed cart model and migrations
  - Story: **VNK-45** — Implement validated cart APIs (add/update/remove/get) using DB cart
  - Task: **VNK-46** — Define cart schema & constraints (max qty, unique cart per customer)

---

## Requirement Traceability Matrix

| Enhancement | Jira Requirement | Acceptance Criteria (summary) | Component(s) | Implementation Task(s) | Test Impact |
|---|---|---|---|---|---|
| VNK-2-ENH-001 | VNK-41 | Quote API blueprint is registered; endpoints reachable | `dev/app.py`, `dev/api/quote_requests.py` | Add blueprint registration; ensure import errors handled consistently | Add/adjust API tests; smoke test route registration |
| VNK-2-ENH-001 | VNK-42 | POST validates payload and persists `QuoteEnquiry`; returns 201 with `quote_id` | `dev/api/quote_requests.py`, `dev/validation.py`, `dev/models.py` | Confirm validation contract; DB write; response contract | Add pytest API tests for POST success + invalid payloads |
| VNK-2-ENH-002 | VNK-44 | DB cart tables exist; constraints enforced | `dev/models.py`, `alembic/versions/*`, `dev/db.py` | Add `Cart`/`CartItem` models; generate Alembic migration | Add migration test (apply/rollback) or schema existence checks |
| VNK-2-ENH-002 | VNK-45 | Cart endpoints support get/add/update/remove with validation | `dev/api/cart.py` (+ potential new `dev/services/cart_service.py`) | Replace in-memory storage; enforce product/qty checks | Add API tests for each endpoint and edge cases |
| VNK-2-ENH-002 | VNK-46 | Unique cart per customer; unique product per cart; qty bounds | `dev/models.py`, migration | Implement constraints + indexes; enforce max qty in validation | Unit tests for validation + DB uniqueness handling |

**Traceability chain format:**

```text
VNK-2-ENH-001
  ↓
VNK-40 / VNK-41 / VNK-42
  ↓
Wire quote blueprint + persist enquiry
  ↓
Flask app + quote API + QuoteEnquiry model
  ↓
Pytest API tests (POST/GET quote enquiries)

VNK-2-ENH-002
  ↓
VNK-44 / VNK-45 / VNK-46
  ↓
DB-backed cart models + validated endpoints
  ↓
Cart API + models + migrations
  ↓
Pytest API tests + regression tests for existing cart routes
```

---

## Existing Architecture (Repository Findings)
### Application structure
- Flask entrypoint: `dev/app.py` (inline landing page HTML via `render_template_string`).
- API blueprints: `dev/api/*`.
- DB: SQLAlchemy via `dev/db.py` and models in `dev/models.py`.
- Migrations: `alembic/` exists but the initial migration (`0001_initial.py`) is empty (`pass`).
- Tests: `dev/tests/*` using Pytest.

### Relevant current behavior
- Quote API exists in `dev/api/quote_requests.py` but **is not registered** in `dev/app.py` blueprint list.
- Cart API (`dev/api/cart.py`) is **in-memory** using global `CARTS = {}` with:
  - `GET /api/cart/<customer_id>`
  - `POST /api/cart/<customer_id>/add`

---

## Component Impact
### Frontend
- The landing page contains a quote form (`<form id="quote-form-element">`) but has **no JS submission**.
- **Planned impact:**
  - Minimal/no HTML changes required for scope, because `dev/api/quote_requests.py` already accepts `request.form`.
  - Optional (if allowed by Jira AC): add a small inline `<script>` to POST form to `/api/quote-enquiries` and show success/error message. If not required by AC, keep frontend unchanged and validate via API.

### Backend / Services
- Quote enquiry: primarily API + model persistence (already partially implemented; missing blueprint registration).
- Cart: requires new data model + service methods (recommended) to avoid fat endpoints.

### Database
- Add new cart tables and constraints.
- Quote enquiry table already exists in `dev/models.py` but may not exist in DB due to empty migration; currently quote API calls `Base.metadata.create_all(bind=engine)`.

### Configuration
- No expected configuration changes for these enhancements.

### Documentation
- Update `README.md` or `dev/README.md` minimally to document cart endpoint contracts and quote submission endpoint(s).

---

## Database Changes
### Summary
**Database changes required** for VNK-2-ENH-002.

### Proposed schema
Add the following models/tables (names can be adjusted to match repo conventions):

1) `carts`
- `id` (uuid string, PK)
- `customer_id` (string, **unique**, required)
- `status` (string; e.g., `ACTIVE`, optional)
- `created_at`, `updated_at`

2) `cart_items`
- `id` (uuid string, PK)
- `cart_id` (FK → carts.id, required)
- `product_id` (FK → products.id, required)
- `quantity` (int, required)
- `unit_price` (numeric(10,2), snapshot from product at time of add/update; optional depending on current patterns)
- `created_at`, `updated_at`

### Constraints / Indexes (VNK-46)
- **Unique cart per customer**: unique index on `carts.customer_id`.
- **Unique product per cart**: unique constraint `(cart_id, product_id)`.
- Quantity constraints:
  - `quantity > 0`
  - max quantity per line: **TBD in Jira AC**. Since human said “accepted”, default to a conservative max (e.g., 999) and confirm in implementation if Jira AC specifies; enforce both in validation and (if DB supports) check constraint.

### Migration approach
- Create a new Alembic revision under `alembic/versions/`.
- Because `0001_initial.py` is empty, ensure:
  - `env.py` loads metadata properly (verify during implementation).
  - Migration includes full DDL for new cart tables.

> Note: Quote enquiries and other existing tables are currently created via `Base.metadata.create_all()` in some modules. During implementation, decide whether to continue relying on `create_all` for dev or move towards explicit migrations; do not expand scope beyond cart tables unless required to make tests pass.

---

## API Changes
### Quote enquiries (VNK-2-ENH-001)
- Ensure endpoints are reachable by registering blueprint:
  - `POST /api/quote-requests` and `POST /api/quote-enquiries` (aliases)
  - `GET /api/quote-requests` and `GET /api/quote-enquiries`

**Request**
- Accept `application/json` body OR form-encoded fields.

**Response**
- `201` on success:
  - `{ "status": "created", "quote_id": "<uuid>", "message": "..." }`
- `400` on validation error: `{ "error": "..." }`

### Cart (VNK-2-ENH-002)
**Backward-compatible endpoints to preserve:**
- `GET /api/cart/<customer_id>` — return cart with items
- `POST /api/cart/<customer_id>/add` — add a line (or increment existing)

**New endpoints (recommended REST additions):**
- `PUT /api/cart/<customer_id>/items/<product_id>` — set quantity
- `DELETE /api/cart/<customer_id>/items/<product_id>` — remove item
- (Optional) `DELETE /api/cart/<customer_id>` — clear cart

**Validation rules (minimal):**
- `customer_id` must be a non-empty string.
- `product_id` must exist in `products` table.
- `quantity` must be a positive integer and not exceed max.
- If product `is_active == false`, block adding/updating (policy accepted earlier).

**Response contract (proposed):**
- Always return a normalized cart object:
  - `{ "customer_id": "...", "items": [{"product_id": "...", "quantity": n, ...}], "totals": {...} }`

---

## Frontend Changes
- **Quote form**: no required UI change to persist data because backend accepts `request.form`.
- Optional improvement (if Jira AC expects end-to-end from UI):
  - Add inline JS to capture submit, POST to `/api/quote-enquiries`, and write status to `#quote-message`.

No other frontend changes planned.

---

## Backend Changes
### VNK-2-ENH-001 (Quote)
- `dev/app.py`
  - Add `quote_requests` / `quote_bp` blueprint registration alongside existing blueprints.
  - Keep current “register individually in try/except” pattern.

- `dev/api/quote_requests.py`
  - Verify naming (`quote_bp`) is imported correctly.
  - Ensure `Base.metadata.create_all()` use does not interfere with migrations/tests.

- `dev/validation.py`
  - Validation already exists; confirm it matches required fields used by UI.

### VNK-2-ENH-002 (Cart)
- `dev/models.py`
  - Add `Cart` and `CartItem` SQLAlchemy models.
  - Add relationships to `Product` if needed.

- `dev/api/cart.py`
  - Replace global in-memory dict with DB operations.
  - Add endpoints for update/remove (plus keep existing get/add).

- (Recommended) `dev/services/cart_service.py` (new)
  - Encapsulate cart CRUD logic:
    - get-or-create cart
    - upsert cart item
    - remove cart item
    - list cart
  - Centralize validation and product lookup.

- `dev/db.py`
  - No functional change planned, but confirm session usage pattern for new service.

---

## Test Impact
### Existing tests likely affected
- Any tests that currently assume cart is in-memory (none identified in `dev/tests` list, but verify during implementation).

### New tests to add (Pytest)
1) Quote enquiry API
- POST success (json)
- POST success (form encoded)
- POST invalid (missing name/mobile/product_category)
- GET list returns created entry

2) Cart API (DB-backed)
- GET empty cart returns empty items
- POST add with valid product_id/quantity creates cart + item
- POST add same product increments or merges (define behavior)
- PUT set quantity updates existing item
- DELETE item removes item
- Validation errors:
  - invalid quantity (0, negative, non-int)
  - product not found
  - product inactive

### Playwright (test-automation)
- Not required unless UI is changed to submit quote form.
- If UI JS is added, add a Playwright smoke test for quote form submission.

### Regression focus
- Ensure existing endpoints remain reachable:
  - `/api/cart/<customer_id>` and `/api/cart/<customer_id>/add`
- Ensure other blueprints continue to register (avoid breaking `dev/app.py` import loop).

---

## Implementation Tasks (Implementation-ready)

### Task list

**T1 — Repo/DB baseline verification**
- **Description:** Verify how DB is initialized in tests/dev, and how Alembic is configured (`alembic/env.py`).
- **Component/files:** `dev/db.py`, `alembic/env.py`, `pytest.ini`, `dev/tests/*`
- **Dependencies:** none
- **Outcome:** clear approach for migrations + test DB setup.

**T2 — VNK-41: Register quote blueprint**
- **Description:** Register `quote_bp` from `dev.api.quote_requests` in `dev/app.py`.
- **Component/files:** `dev/app.py`
- **Dependencies:** none
- **Outcome:** `/api/quote-enquiries` and `/api/quote-requests` routes available.

**T3 — VNK-42: Quote enquiry persistence/validation hardening**
- **Description:** Confirm validation + persistence behavior; ensure consistent response codes/messages.
- **Component/files:** `dev/api/quote_requests.py`, `dev/validation.py`, `dev/models.py`
- **Dependencies:** T2
- **Outcome:** POST creates `QuoteEnquiry` row; GET lists rows.

**T4 — VNK-46: Define cart schema & constraints**
- **Description:** Design cart tables, constraints (unique cart per customer, unique product per cart), qty bounds.
- **Component/files:** `dev/models.py`
- **Dependencies:** T1
- **Outcome:** SQLAlchemy models reflect required constraints/relationships.

**T5 — VNK-44: Alembic migration for cart tables**
- **Description:** Create migration to add `carts` and `cart_items` tables.
- **Component/files:** `alembic/versions/<new>.py`, maybe `alembic/env.py`
- **Dependencies:** T4
- **Outcome:** `alembic upgrade head` creates schema in SQLite.

**T6 — VNK-45: Implement DB-backed cart endpoints**
- **Description:** Replace in-memory cart with DB CRUD; keep old routes and add REST endpoints.
- **Component/files:** `dev/api/cart.py`; new `dev/services/cart_service.py` (recommended)
- **Dependencies:** T4/T5
- **Outcome:** cart endpoints operate on DB; validation enforced.

**T7 — Tests for quote + cart**
- **Description:** Add/extend pytest coverage for both features.
- **Component/files:** new tests under `dev/tests/` (e.g., `test_quote_enquiries.py`, `test_cart_api.py`)
- **Dependencies:** T2, T3, T6
- **Outcome:** tests pass locally + in CI.

**T8 — Docs updates**
- **Description:** Document endpoints and example payloads.
- **Component/files:** `README.md` and/or `dev/README.md`
- **Dependencies:** T6
- **Outcome:** developer clarity, easier manual testing.

---

## Dependencies
- SQLAlchemy + Flask session usage pattern (`SessionLocal()` context manager is used in quote API).
- SQLite constraints support (some CHECK constraints are limited; enforce qty bounds at validation layer regardless).
- Alembic configuration: current initial migration is empty; migration strategy must be validated.

---

## Risks
- **Alembic drift risk:** Because `0001_initial.py` is empty, DB schema may be created via `Base.metadata.create_all()` in runtime modules. This can cause inconsistent environments across dev/test.
  - Mitigation: keep cart migration self-contained and ensure tests use migrated schema.

- **Backward compatibility risk:** Existing cart clients may rely on old response shape (currently returns raw dict).
  - Mitigation: preserve routes and provide response compatibility layer or documented breaking change with versioning (prefer compatibility).

- **Concurrency risk:** DB-backed cart reduces multi-worker issues, but concurrent updates can still race.
  - Mitigation: use unique constraints + retry on integrity errors; keep operations transactional.

- **Blueprint registration import errors:** The current blueprint registration loop catches exceptions; adding quote import must follow the same pattern.
  - Mitigation: minimal change; add coverage test that app starts and route exists.

---

## Implementation Sequence (Recommended)
1. **T1** baseline verification (DB + migrations + tests).
2. **T2** register quote blueprint.
3. **T3** quote persistence/validation checks.
4. **T4** add cart models + constraints.
5. **T5** create Alembic migration for cart.
6. **T6** implement DB-backed cart endpoints.
7. **T7** add/update tests.
8. **T8** docs update.

---

## Definition of Done
- Quote enquiry endpoints are registered and reachable:
  - `POST /api/quote-enquiries` returns **201** and persists data.
  - `GET /api/quote-enquiries` returns list including newly created entry.
- Cart is persisted to DB:
  - `GET /api/cart/<customer_id>` works for new and existing carts.
  - Add/update/remove endpoints enforce validation and constraints.
  - Existing routes (`/add`) continue to function.
- Alembic migration exists and applies cleanly on SQLite.
- Automated tests:
  - New/updated pytest tests pass.
  - No regressions in existing tests.
- Documentation updated with endpoint usage.

