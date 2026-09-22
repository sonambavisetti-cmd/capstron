# Implementation Plan — VNK-112 (Storefront UI (MVP))

## Objective
Deliver a **minimal storefront UI** for Vinayaka File Works that enables a non-technical user to:
1) browse products (list + detail),
2) add/update/remove items in a cart with totals,
3) complete checkout (delivery address + transport mode),
4) place an order and view an order confirmation.

This enhancement introduces a lightweight UI surface while preserving the existing REST API-first architecture.

## Scope (Validated)
### In scope
- **Server-rendered storefront UI** (no separate SPA repo) using FastAPI/Flask-served templates.
- Pages:
  - Product list
  - Product detail
  - Cart (view/update/remove)
  - Checkout (collect delivery details and transport mode)
  - Order confirmation (order id + summary)
- Shared layout shell (header/nav/footer) and UI routes.
- UI-to-API integration via a small internal client wrapper with consistent error handling.
- Transport/shipping mode options (MVP):
  - **Customer pickup**
  - **Local transport**
  - **Courier**
- “All required API content” to support checkout submission:
  - Ensure the backend can accept and persist **delivery address** + **transport mode** on order creation.
  - Ensure order lookup returns these fields for confirmation display.

### Out of scope
- Payments UI and real payment provider integration.
- Authentication / user accounts.
- Admin UI.
- Advanced search/filtering, promotions, tax/GST, shipping cost calculation (separate enhancements).

## Requirement Traceability (preserve chain)
Approved Enhancement → Jira Requirement → Implementation Task → Component → Test Impact

| Approved Enhancement | Jira Epic | Jira Requirement | Implementation Task | Component(s) | Test Impact |
|---|---|---|---|---|---|
| VNK-VNK-1-ENH-001 | VNK-112 | VNK-116 | Define UI routes, navigation, shared layout shell | `dev/app/main.py` (mount routes), `dev/templates/*`, `dev/static/*` | Playwright: navigation smoke; template render tests |
| VNK-VNK-1-ENH-001 | VNK-112 | VNK-117 | Implement UI→API client wrapper (catalog/cart/orders) + error handling | `dev/app/ui/api_client.py` (new), `dev/app/ui/errors.py` (new) | Unit: client error handling; integration: UI pages call APIs |
| VNK-VNK-1-ENH-001 | VNK-112 | VNK-113 | Product browsing UI (list + detail) | `dev/app/ui/routes_products.py` (new), templates | Playwright: list loads; detail loads; add-to-cart flow |
| VNK-VNK-1-ENH-001 | VNK-112 | VNK-114 | Cart UI (view/update/remove + totals) | `dev/app/ui/routes_cart.py` (new), templates | Playwright: update qty; remove item; totals visible |
| VNK-VNK-1-ENH-001 | VNK-112 | VNK-115 | Checkout UI (address + transport mode + place order) | `dev/app/ui/routes_checkout.py` (new), templates; backend order schema | API tests for `POST /api/orders` payload; Playwright: checkout submit |

## Existing Architecture (Relevant)
- Backend service under `dev/`.
- **FastAPI app** entry: `dev/app/main.py` exposing JSON APIs under `/api/*`.
- **Flask blueprints** also present under `dev/api/*.py` (potentially legacy/parallel).
- Persistence: SQLAlchemy + Alembic, SQLite (`dev.db`).
- Templates: `dev/templates/` contains an invoice template stub; no storefront templates exist yet.
- Testing:
  - `dev/tests/` (pytest)
  - `test-automation/` (Playwright) exists for UI automation.

## Planned UI Architecture Decision
Because the repository has **no dedicated frontend**, the MVP storefront will be implemented as **server-rendered HTML templates** served by the existing backend service.

- Add a `ui` module under the FastAPI app (preferred) and serve:
  - Jinja2 templates from `dev/templates/storefront/`
  - Static assets from `dev/static/storefront/`
- UI routes will call existing `/api/*` endpoints via an internal client wrapper.

Rationale: minimal deployment complexity, aligns with current single-service architecture.

## Affected Components
### New / updated (expected)
- **UI routing & layout**
  - `dev/app/main.py` (mount UI router + template/static config)
  - `dev/app/ui/` (new package)
  - `dev/templates/storefront/*.html` (new)
  - `dev/static/storefront/*` (new)

### Backend API contract support
- Orders API: `POST /api/orders` and `GET /api/orders/{id}` must support:
  - `delivery_address` (structured or string)
  - `transport_mode` (enum-like with 3 allowed values)
- Data layer:
  - `dev/models.py` (if new columns are required)
  - Alembic migration under `dev/ops/alembic/versions/` (path may vary)
  - `dev/schemas/*` (Pydantic schemas used by FastAPI)
  - `dev/services/order_service.py` (order creation logic)

## Frontend Changes (Server-rendered UI)
### UI routes (new)
- `GET /` → redirect to `/products`
- `GET /products` → product list
- `GET /products/{id}` → product detail
- `POST /cart/add` → add item to cart (uses API)
- `GET /cart` → cart view
- `POST /cart/update` → update quantities
- `POST /cart/remove` → remove item
- `GET /checkout` → checkout form
- `POST /checkout` → place order
- `GET /order/{id}` → confirmation page

### UI templates (new)
- `dev/templates/storefront/_layout.html` (shared shell)
- `dev/templates/storefront/products.html`
- `dev/templates/storefront/product_detail.html`
- `dev/templates/storefront/cart.html`
- `dev/templates/storefront/checkout.html`
- `dev/templates/storefront/order_confirmation.html`
- `dev/templates/storefront/_error.html` (friendly error rendering)

### UX notes (MVP)
- Use HTML forms + server-side rendering; keep JS optional/minimal.
- Display errors returned by API (validation, out-of-stock, etc.).

## Backend Changes (to support checkout data)
### Order payload and persistence
- Add/confirm fields:
  - `transport_mode`: string constrained to {`CUSTOMER_PICKUP`, `LOCAL_TRANSPORT`, `COURIER`} (wire format) while UI labels show friendly names.
  - `delivery_address`: MVP as a single text field (e.g., multiline) unless schema already supports structured address.

### Validation
- Backend validates transport_mode is one of the allowed values.
- If transport_mode is `CUSTOMER_PICKUP`, delivery_address may be optional (MVP decision; enforce consistently).

### Compatibility
- Must not break existing API clients/tests.
- If existing order model already has `shipping_address` or similar, map UI fields accordingly and avoid new DB columns.

## API Changes
### If required by current API contract (to be validated during implementation)
- Update `POST /api/orders` request schema to include:
  - `delivery_address`
  - `transport_mode`
- Update `GET /api/orders/{id}` response schema to include the same fields so UI confirmation can render them.

> Note: During implementation step, the team should inspect the current `POST /api/orders` payload and extend it minimally to include these fields without changing existing required fields.

## Database Changes
- **Likely**: add two columns to the `orders` table if not present:
  - `delivery_address` (TEXT)
  - `transport_mode` (VARCHAR)
- Alembic migration required.
- If an existing equivalent exists (e.g., `shipping_address`), reuse and avoid migrations.

## Test Impact
### Pytest (backend)
- Schema validation tests:
  - `POST /api/orders` accepts the 3 transport modes.
  - Rejects invalid mode.
  - Verifies persisted values returned by `GET /api/orders/{id}`.

### UI automation (Playwright)
- Add new UI specs under `test-automation/`:
  - Navigate `/products` list, open detail.
  - Add to cart, update qty, remove.
  - Checkout with each transport mode (at least 1 happy path + 1 mode-variation smoke).
  - Assert confirmation page renders order id and summary.

### Non-functional
- Basic accessibility: forms have labels; errors are visible.

## Implementation Tasks (by Jira item)
### VNK-116 — UI routes/navigation and shared layout shell
1. Decide UI integration layer: FastAPI router + Jinja2 templates.
2. Add template loader + static files mount in `dev/app/main.py`.
3. Create shared layout template and nav links (Products, Cart).
4. Add root redirect and 404/friendly error page.

### VNK-117 — UI-to-API client wrapper
1. Create `api_client` with functions:
   - `list_products()`
   - `get_product(id)`
   - `get_cart(cart_payload)` / `price_cart(...)`
   - `create_order(order_payload)`
   - `get_order(id)`
2. Standardize error capture:
   - Network errors
   - Non-2xx responses mapped to UI error pages/messages
3. Add unit tests for error mapping.

### VNK-113 — Product browsing UI
1. Implement `/products` and `/products/{id}` routes.
2. Render product fields (name, description, unit price, image if available).
3. Add “Add to cart” form.

### VNK-114 — Cart UI
1. Implement cart session strategy (MVP):
   - Use signed cookie/session OR hidden form state (to be selected during implementation).
2. Render cart items, quantities, subtotal/total.
3. Add update/remove actions and error handling.

### VNK-115 — Checkout UI
1. Implement checkout form:
   - delivery address
   - transport mode (3 options)
2. On submit, call `POST /api/orders`.
3. Redirect to order confirmation.
4. Render order confirmation from `GET /api/orders/{id}`.

## Dependencies
- **API contract confirmation**: confirm current `POST /api/orders` expected fields and extend schema without breaking existing callers.
- **Template engine**: ensure Jinja2 dependency is present (FastAPI typically uses `jinja2`). If missing, add to requirements in implementation PR.
- **Session/cart state mechanism**: must align with existing `/api/cart` design (it appears to be a pricing endpoint requiring cart items payload).

## Risks & Mitigations
- **Dual frameworks (FastAPI + Flask) ambiguity**: UI should be attached to the active runtime entrypoint. Mitigation: implement UI in FastAPI `dev/app/main.py` and ensure it is the documented entry.
- **Product schema mismatch (name vs title)**: UI may break if Flask routes are used. Mitigation: UI targets FastAPI endpoints; add a small compatibility mapping in API client if needed.
- **Cart persistence**: No existing persistent cart model. Mitigation: keep cart state in session/cookie for MVP.
- **CSS/asset scope creep**: keep styling minimal.

## Implementation Sequence (recommended)
1. Add UI plumbing (templates/static + router mounting) — VNK-116.
2. Add API client wrapper — VNK-117.
3. Build product list/detail pages — VNK-113.
4. Implement cart flow end-to-end — VNK-114.
5. Implement checkout + order confirmation; update API/DB schema if required — VNK-115.
6. Add/expand automated tests (pytest + Playwright).

## Definition of Done
- UI pages are accessible and functional:
  - browse products, view detail, manage cart, checkout, see confirmation.
- Transport mode includes all 3 options.
- Order creation persists and returns delivery address + transport mode (or maps to existing fields).
- No existing API endpoints are broken; existing tests pass.
- New tests added for UI flows (Playwright) and API schema validation (pytest).
- **Planning artifact only** committed to `dev/impl-plan.md` and reviewed.
