# Implementation Plan — VNK-119 — Checkout Form HTML5 Validation (ENH-001)

## Objective
Implement **checkout form UX/validation improvements** for the Storefront MVP so customers enter correct contact/address details the first time.

Specifically (per approved enhancement **VNK-VNK-1-ENH-001**):
- Add **HTML5 input types/constraints** (email/tel, patterns, min/max lengths, required flags)
- Add **inline validation message placeholders** (using browser-native validation UI plus template-level hints)
- **Preserve submitted values** on validation failure (server-side re-render with prior values)

## Scope (validated)
### In scope (APPROVE SELECTED)
Only the following approved enhancement is in scope:
- **VNK-VNK-1-ENH-001** — Checkout UX / Validation

Includes:
- Checkout template updates (`dev/templates/storefront/checkout.html`)
- Checkout submit flow updates to support re-rendering with values/errors (`dev/app/ui/routes.py`)
- Minimal server-side validation for required fields (to ensure value preservation is exercised even if browser-side validation is bypassed)
- Tests to cover the validation behavior and value preservation

### Out of scope
- **ENH-002** generic error page replacement with inline banner for API failures (explicitly excluded by prior decision)
- Transport detail capture, GST/tax UI, payment method selection, invoice links, search/filter, cart UX changes
- Database/API contract changes (unless required to support validation error handling; not expected for ENH-001)

## Requirement traceability (preserve chain)
Approved Enhancement → Jira Requirement → Implementation Task → Component → Test Impact

| Approved Enhancement | Jira Epic | Jira Requirement | Jira Task | Implementation Task (this plan) | Component(s) | Test Impact |
|---|---|---|---|---|---|---|
| VNK-VNK-1-ENH-001 | VNK-118 | VNK-119 | VNK-120 | Add HTML5 field types/constraints + inline help text blocks | `dev/templates/storefront/checkout.html` | Template render test; UI automation: browser blocks invalid input |
| VNK-VNK-1-ENH-001 | VNK-118 | VNK-119 | VNK-121 | Preserve submitted values when server-side validation fails (re-render checkout with values + errors) | `dev/app/ui/routes.py`, `dev/templates/storefront/checkout.html` | Unit/integration test: POST checkout invalid → 200 with preserved values |

## Existing architecture (relevant)
- UI is server-rendered via **FastAPI APIRouter**: `dev/app/ui/routes.py`
- Templates via **Jinja2**: `templates = Jinja2Templates(directory="dev/templates")`
- Checkout page and submit endpoints:
  - `GET /checkout` → renders `dev/templates/storefront/checkout.html`
  - `POST /checkout` → builds order payload and calls `_client(request).create_order(payload)`

## Affected components
### Frontend (templates)
- `dev/templates/storefront/checkout.html`

### Backend (UI router)
- `dev/app/ui/routes.py`:
  - `checkout_page()` (GET)
  - `checkout_submit()` (POST)

### Tests
- Add/adjust pytest tests under `dev/tests/` (existing suite present)
- Optional: update Playwright specs under `test-automation/` if present (not required to satisfy ENH-001, but recommended)

## Frontend changes (server-rendered checkout)
### 1) Add HTML5 input types/constraints
Update inputs in `checkout.html`:
- **Full name**
  - `required`
  - `minlength` (e.g., 2)
  - `maxlength` (e.g., 100)
  - `autocomplete="name"`
- **Phone**
  - `type="tel"`
  - `inputmode="tel"`
  - `autocomplete="tel"`
  - pattern for India-friendly digits (example): `pattern="[0-9+\-() ]{7,15}"`
  - `minlength`/`maxlength` aligned with pattern intent
  - keep optional (per current behavior) unless product owner wants it required
- **Email**
  - `type="email"`
  - `autocomplete="email"`
  - optional
- **Address line 1 / City / State / Postal code / Country**
  - Ensure `required` stays on required fields
  - Add `minlength`/`maxlength`
  - Postal code:
    - `inputmode="numeric"`
    - `pattern="[0-9]{6}"` (India PIN)
    - `maxlength="6"`

### 2) Inline validation messages / hints
Because browser-native validation messaging is user-agent controlled, add lightweight inline hints:
- Add `<small class="hint">…</small>` under phone/email/pincode fields.
- Add a template block for server-side errors:
  - A top-level summary (existing `{% if error %}` block can be reused)
  - Field-level error placeholders if implementing structured errors (recommended)

### 3) Preserve submitted values on re-render
Modify `checkout.html` inputs to use Jinja values:
- `value="{{ form.full_name | default('') }}"`
- For text inputs; for `<select>`, mark selected option based on `form.transport_mode`.

## Backend changes (UI router)
### 1) Add a simple form model for templating
In `dev/app/ui/routes.py`, introduce a small internal dict (no new module required in planning, but recommended structure):
- `form_data = {"full_name": ..., "phone": ..., "email": ..., ...}`
- `form_errors = {"full_name": "...", "postal_code": "..."}`

### 2) Server-side validation (minimal)
Add validation in `checkout_submit()` before calling API:
- Required fields: `full_name`, `address_line1`, `city`, `state`, `postal_code`, `transport_mode`
- Email: if provided, basic format check (or rely on Pydantic/email-validator only if already present). Keep minimal.
- Phone: if provided, validate against same regex as template pattern (keep in one place to avoid drift).
- Postal code: validate 6 digits.

If validation fails:
- Re-price cart via `_client(request).price_cart(items)` so summary remains visible
- Return `TemplateResponse("storefront/checkout.html", {..., "form": form_data, "errors": form_errors})`
- HTTP 200 (or 422) — choose 200 for simplicity with SSR

> Note: This is not ENH-002; this is only for **form validation failures prior to API call**.

### 3) GET /checkout populates empty form defaults
Update `checkout_page()` to provide:
- `form` defaults: `{"country": "IN"}`
- `errors`: `{}`

## API changes
None expected.
- `POST /checkout` continues to call existing `_client(request).create_order(payload)`.
- No change to API payload schema is required for ENH-001.

## Database changes
None.

## Test impact
### Pytest (recommended minimal coverage)
Add tests validating:
1. `GET /checkout` renders and includes HTML5 attributes (smoke assertion on `type="email"`, `type="tel"`, `pattern=` for pin)
2. `POST /checkout` with invalid postal code (e.g., `123`) re-renders checkout (status 200) and preserves previously entered values
3. `POST /checkout` with invalid email (e.g., `abc`) re-renders with error and preserved values

Implementation approach:
- Use FastAPI `TestClient` against app entry (whichever is used by existing tests). If a UI router is mounted, call `/checkout`.
- Mock `_client(request).create_order` to ensure it is **not called** on validation error.

### Playwright (optional)
- Verify browser blocks invalid email/phone/pincode client-side.

## Implementation tasks
### Jira VNK-120 — Update checkout template
1. Add `form` + `errors` template variables support
2. Add HTML5 input types and attributes:
   - email/tel/numeric patterns
   - minlength/maxlength
   - autocomplete/inputmode
3. Add inline hints for phone/email/pincode
4. Ensure transport mode retains selected option on re-render

### Jira VNK-121 — Preserve values on validation failure
1. Implement server-side validation helpers (prefer pure functions inside `routes.py` to avoid new modules)
2. On validation failure:
   - compute `summary` (if items present)
   - return checkout template with populated `form` and `errors`
3. Ensure existing successful submission path is unchanged

## Dependencies
- None new expected.
- If robust email validation is required beyond a simple regex, confirm whether `email-validator` is already available via Pydantic extras; otherwise keep minimal.

## Risks & mitigations
- **Duplication of validation rules** (template vs server): Keep regex/pattern constants in one place (server), and inject pattern strings into template context.
- **Breaking existing template expectations**: Ensure `checkout.html` works whether `form`/`errors` provided or not using `default()`.
- **Cart pricing API failure during re-render**: If `_client.price_cart` fails, render checkout with `summary=None` and an error banner while still preserving fields.

## Implementation sequence
1. Update `checkout_page()` context to include `form` and `errors`.
2. Update `checkout.html` to bind values and add HTML5 constraints.
3. Add server-side validation in `checkout_submit()` and re-render on failure.
4. Add/update pytest tests for validation + value preservation.

## Definition of Done
- `dev/templates/storefront/checkout.html` uses HTML5 types/constraints for email/phone/postal code and includes user hints.
- Validation failures re-render checkout with:
  - visible error message(s)
  - previously entered values preserved
  - transport mode selection preserved
- Happy path checkout continues to create order and redirect to confirmation.
- Automated tests added/updated and passing.
- Only planning artifact changed/committed: `dev/impl-plan.md`.
