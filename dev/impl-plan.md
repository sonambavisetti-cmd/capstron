# Implementation Plan — VNK-126 / VNK-127 / VNK-128 / VNK-129 (VNK-VNK-2-ENH-001)

## Objective
Improve the **Landing Page Quote Enquiry form** UX by adding:
- **Client-side validation** (required fields + basic email + digit-only phone)
- **Inline, field-level error messages**
- **Submit-in-progress state** (disable button + progress label to prevent duplicates)
- **Clear server error feedback** (general error + map field errors when provided)

This plan is implementation-ready and limited to the **approved enhancement** below.

---

## Scope
### In scope (APPROVE SELECTED)
- **Approved Enhancement:** `VNK-VNK-2-ENH-001` — UI / Quote form validation & UX
- **Jira Epic:** VNK-126 — Improve Quote Enquiry Form Validation & UX
- **Jira Stories:**
  - VNK-127 — Inline validation on the quote enquiry form
  - VNK-128 — Prevent duplicate submits + progress state
  - VNK-129 — Clear server error feedback when submission fails
- **Jira Tasks:**
  - VNK-130 — Update landing page quote form markup to support inline errors
  - VNK-131 — Implement client-side quote form validation logic
  - VNK-132 — Implement submit-in-progress state (disable + progress label)
  - VNK-133 — Handle server-side validation errors (map to fields where possible)

### Out of scope
- Product browsing UI, mobile menu/accessibility work, quote endpoint naming standardization (other enhancements)
- Any new admin UI or workflow
- Backend validation changes unless required to support better error messages (see Backend Changes)

---

## Scope Validation (approved assumptions)
Per user direction, proceed with the following assumptions:
- **Quote form fields (assumed current landing page fields):**
  - `name`
  - `mobile_number` (phone)
  - `email`
  - `message` (requirements/details)
- **Phone validation rule:** digit-only; reject if contains non-digits; require minimum length **10** digits.
- **Post-success behavior:** keep field values as-is; show success message (do not reset the form).

If the actual `dev/app.py` markup differs (field names/ids), align implementation to the real fields while keeping the same validation intent.

---

## Requirement Traceability

| Approved Enhancement | Jira Requirement | Implementation Task(s) | Component(s) | Test Impact |
|---|---|---|---|---|
| VNK-VNK-2-ENH-001 | VNK-127 (Story) inline validation + field errors | VNK-130, VNK-131 | `dev/app.py` (landing page HTML/JS) | Add/update Playwright tests for inline validation; unit-style JS tests are not present today |
| VNK-VNK-2-ENH-001 | VNK-128 (Story) prevent duplicate submits | VNK-132 | `dev/app.py` (landing page JS/CSS) | Playwright: verify button disabled + label change during request |
| VNK-VNK-2-ENH-001 | VNK-129 (Story) clear server errors | VNK-133 | `dev/app.py` (landing page JS) and possibly `dev/api/quote_requests.py` (optional) | Playwright/API tests for failure cases and error rendering |

Traceability chain:

```text
VNK-VNK-2-ENH-001
  ↓
Epic VNK-126
  ↓
Story VNK-127 → Tasks VNK-130, VNK-131 → dev/app.py (form markup + JS validation) → Playwright tests
Story VNK-128 → Task VNK-132 → dev/app.py (submit state) → Playwright tests
Story VNK-129 → Task VNK-133 → dev/app.py (server error mapping) (+ optional API tweaks) → Playwright/API tests
```

---

## Existing Architecture (relevant)
- Single Flask app under `dev/`.
- Landing page rendered inline via `render_template_string(...)` in `dev/app.py` at route `/`.
- Quote submission currently performed by in-page JS `fetch(...)` to `POST /api/quote-enquiries`.
- Quote API implemented in `dev/api/quote_requests.py` and persisted via `QuoteEnquiry` model in `dev/models.py`.

---

## Affected Components
### Frontend (server-rendered landing page)
- `dev/app.py`
  - Quote form markup (add inline error containers, consistent IDs/names)
  - Quote form JS submit handler (validation, submit state, error mapping)
  - Minimal CSS adjustments (error styles, disabled button)

### Backend (optional, only if needed for clearer errors)
- `dev/api/quote_requests.py`
  - If current API returns only generic errors, optionally standardize error JSON shape to support field mapping.

### Test automation
- `test-automation/` Playwright tests (exact path to be confirmed in repo)
- Possibly `dev/tests/` API tests if server error shapes are adjusted

---

## Frontend Changes (detailed)

### 1) Form markup updates (VNK-130)
In `dev/app.py` within the quote form HTML:
- Ensure each input/textarea has:
  - Stable `id` and `name` matching the JSON payload keys (`name`, `mobile_number`, `email`, `message`).
  - `aria-invalid="true|false"` toggled by JS.
  - `aria-describedby` referencing an inline error element.
- Add an inline error container per field, e.g.:
  - `<div class="field-error" id="error-name" role="alert"></div>`
  - `<div class="field-error" id="error-mobile_number" role="alert"></div>`
  - `<div class="field-error" id="error-email" role="alert"></div>`
  - `<div class="field-error" id="error-message" role="alert"></div>`
- Add a general form message container (already exists) and ensure it supports:
  - success (green)
  - error (red)

### 2) Client-side validation rules (VNK-131)
Implement a small validation module (inline JS functions in `dev/app.py`):
- `validateRequired(value)` for all fields.
- `validateEmail(value)`:
  - basic pattern (e.g., `/^\S+@\S+\.\S+$/`) OR use `type="email"` + JS check.
- `validatePhoneDigits(value)`:
  - digits-only: `/^\d+$/`
  - length >= 10.

Validation behavior:
- On submit: validate all fields; show inline errors; prevent submit if any errors.
- On input/blur: clear field error when valid; optionally validate on blur for immediate feedback.

### 3) Submit-in-progress state (VNK-132)
During the async `fetch` call:
- Disable submit button.
- Change button label to “Submitting…” (or similar).
- Prevent multiple submissions:
  - ignore subsequent submits while `isSubmitting === true`.
- Always restore state in `finally` block:
  - re-enable button
  - restore original label

### 4) Server error handling + mapping (VNK-133)
When the server responds with non-2xx:
- Prefer to parse JSON error response.
- Support the following response shapes (be tolerant):
  1. `{ "message": "..." }`
  2. `{ "error": "..." }`
  3. `{ "errors": { "field": "message", "field2": "message" }, "message": "..." }`
  4. `{ "errors": [{"field":"email","message":"Invalid"}] }`

Mapping strategy:
- If field errors are present, display them inline for matching field keys.
- Otherwise show a general error message.
- Keep existing values (no reset) even on success; on success show a success message.

---

## Backend / API Changes

### Default approach (no backend changes)
- Implement client-side validation and resilient error parsing without requiring API changes.

### Optional improvement (only if quick + low risk)
If `dev/api/quote_requests.py` currently returns plain text or inconsistent errors, standardize failure responses to:

```json
{ "message": "Validation failed", "errors": { "email": "Invalid email" } }
```

This is optional and should be done only if it does not expand scope beyond VNK-VNK-2-ENH-001.

---

## Database Changes
- None.

---

## Test Impact

### Playwright (UI) tests (preferred)
Add/update tests to cover:
1. **Required validation**: submit empty form → inline errors shown for each required field.
2. **Phone validation**: enter non-digit phone or <10 digits → phone field error shown.
3. **Email validation**: invalid email → email field error shown.
4. **Submit progress**: during submission, button is disabled and label changes; after completion it re-enables.
5. **Server error rendering**: simulate server error (route interception/mocking or point to test API) and verify general error message and/or field mapping.
6. **Success**: success message shown and values remain.

### API tests (only if backend error format changes)
- Update/add pytest tests to assert consistent error JSON.

---

## Implementation Tasks (mapped to Jira)

### VNK-130 — Update landing page quote form markup
- Update HTML structure to include per-field error elements + ARIA attributes.
- Add CSS for `.field-error` and invalid field styles.

### VNK-131 — Implement client-side validation logic
- Add JS functions to validate required/email/phone.
- Add event listeners for `submit`, and optionally `blur/input` for live feedback.
- Ensure errors clear when corrected.

### VNK-132 — Implement submit-in-progress state
- Introduce `isSubmitting` guard.
- Disable/enable button and update label around `fetch`.

### VNK-133 — Handle server-side validation errors
- Parse non-2xx responses.
- Map server-provided field errors to inline errors.
- Provide fallback general error.

---

## Dependencies
- Confirm actual form field IDs/names in `dev/app.py` (planned work aligns to current markup).
- Confirm Playwright is used and runnable under `test-automation/` in this repo.

---

## Risks / Mitigations
- **Field name mismatch** (UI keys vs API keys): mitigate by aligning `name` attributes and JSON payload keys to backend expectations.
- **Inconsistent backend errors**: mitigate by tolerant parsing; optional backend standardization if needed.
- **Inline HTML in `dev/app.py`** can get large/unwieldy: keep changes minimal; no refactor into templates in this scope.

---

## Implementation Sequence
1. Inspect existing quote form markup + JS in `dev/app.py` and align assumed field list.
2. Implement VNK-130 markup changes + basic CSS.
3. Implement VNK-131 client validation + inline errors.
4. Implement VNK-132 submit-in-progress state.
5. Implement VNK-133 server error parsing/mapping.
6. Add/update Playwright tests.
7. Run tests locally (Playwright + pytest if applicable).

---

## Definition of Done
- Quote form prevents invalid submissions with clear inline messages.
- Phone accepts **digits only** and requires **>=10** digits.
- Submit button disables and shows progress during request; duplicate submits prevented.
- Server failures show clear general error and map field errors where available.
- On success, form values remain and a success message is shown.
- All relevant automated tests pass.
- Only planning artifacts committed to `feature/VNK-126`.
