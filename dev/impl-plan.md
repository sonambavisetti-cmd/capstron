# Implementation Plan — VNK-VNK-2-ENH-001 (Client-side validation + inline field errors)

## Objective
Improve the quote enquiry form UX on the landing page by adding **lightweight client-side validation** and **field-level inline error messaging** so users can correct mistakes before the API request is sent.

Human-approved scope: **VNK-VNK-2-ENH-001 only**.

---

## Scope (Validated)
### In scope
- Client-side validation for the quote enquiry form on `/`:
  - Required-field validation (do not submit when invalid)
  - Email format validation
  - Phone number validation: digits-only and length boundaries (per approved AC)
- Inline, per-field error messages (visible near the corresponding input)
- Preserve existing “Sending…” message behavior; additionally ensure **no request is sent** when validation fails.

### Out of scope
- Backend/API changes (including structured validation errors) — belongs to **VNK-VNK-2-ENH-002**
- Database changes
- New pages/templates, UI redesign, or admin workflows

---

## Requirement Traceability

Approved Enhancement → Jira Requirement → Implementation Task → Component → Test Impact

| Approved Enhancement | Jira Requirement | Implementation Task | Component(s) | Test Impact |
|---|---|---|---|---|
| VNK-VNK-2-ENH-001 | **Epic:** VNK-126 Improve Quote Enquiry Form Validation & UX | Plan/coordinate work under epic | Jira only | None |
| VNK-VNK-2-ENH-001 | **Story:** VNK-134 Add client-side validation with inline errors for quote enquiry form | Deliver client-side validation + inline errors + prevent submit | `dev/app.py` (inline HTML/CSS/JS on `/`) | Update/add UI-level tests (or pytest route tests where feasible) |
| VNK-VNK-2-ENH-001 | **Subtask:** VNK-135 Implement client-side validation rules for quote enquiry form fields | Add JS validation functions and checks prior to fetch | `dev/app.py` JS section | UI tests: validation prevents network request |
| VNK-VNK-2-ENH-001 | **Subtask:** VNK-136 Add inline field-level error message UI for quote enquiry form | Add error placeholders, styles, and per-field rendering | `dev/app.py` HTML/CSS/JS | UI tests: inline errors rendered and cleared |

---

## Existing Architecture (Relevant)
- Flask server-rendered landing page is implemented inline via `render_template_string` in:
  - `dev/app.py` route `@app.route('/')`
- Quote enquiry submission uses frontend JS `fetch` to:
  - `POST /api/quote-enquiries` (also `/api/quote-requests` may exist as alias)
- Current HTML form includes `novalidate` and relies on backend validation.

---

## Affected Components
### Frontend (primary)
- `dev/app.py`:
  - HTML for quote enquiry form fields
  - Inline CSS for styling
  - Inline JS for submit handler and status message

### Backend
- **No change planned** for ENH-001.

### API
- No contract changes planned.

### Database
- No changes.

---

## Frontend Changes (Implementation Details)

### 1) Add inline error UI placeholders (VNK-136)
For each input/textarea in the quote form, add:
- A small `<div class="field-error" id="err-<field>"></div>` placed close to the field.
- Ensure errors are hidden when empty.

Suggested field ids (align with existing markup as much as possible):
- `name` → `err-name`
- `mobile_number` (or `phone`) → `err-mobile_number`
- `email` → `err-email`
- `product_type` / `service` (whatever exists in form) → `err-...`
- `requirements` / `message` (textarea) → `err-...`

### 2) Add lightweight client-side validation (VNK-135)
Add JS functions:
- `setFieldError(fieldId, message)` / `clearFieldError(fieldId)`
- `validateRequired(value)`
- `validateEmail(value)` using simple regex (non-exhaustive but practical)
- `validatePhone(value)`:
  - Strip spaces/hyphens? (keep aligned with AC “digits + length”; recommended: allow user separators but validate digits-only after normalization)
  - Enforce min/max length boundaries (see “Validation Rules”)

Ensure the submit handler:
- Validates all fields
- Populates inline errors
- Focuses the **first invalid field**
- Returns early **without calling fetch** when invalid

### 3) Inline error styling
Add minimal CSS (within the existing `<style>`):
- `.field-error { color: #b42318; font-size: 0.9rem; margin-top: 6px; }`
- Optional input error style:
  - `.input-error { border-color: #b42318; outline-color: #b42318; }`

### 4) Error clearing behavior
- On user input/change, clear that field’s error and remove `input-error` class.
- On successful submit, clear all field errors.

---

## Validation Rules (per Story AC)
> Note: phone rules were previously marked as needing clarification; user approved to proceed. This plan will implement explicit boundaries and document them for review.

- **Required fields:** all form fields marked required in the UI must be non-empty (trimmed).
- **Email:** must match a simple pattern like `^[^\s@]+@[^\s@]+\.[^\s@]+$`.
- **Phone:**
  - Normalize by removing spaces and hyphens (e.g., `value.replace(/[\s-]/g,'')`) then validate.
  - Must be digits-only after normalization: `^\d+$`
  - Length boundaries: **min 10, max 15** digits (typical E.164-ish upper bound).

If the team expects India-specific numbers only, adjust to exactly 10 digits; but for now keep 10–15 as a safe MVP unless Jira AC specifies otherwise.

---

## Backend / API / DB Changes
- **Backend:** none
- **API:** none
- **DB:** none

---

## Test Impact

### Existing tests
- Any existing API tests should remain unchanged.

### New/updated tests (recommended)
Because the validation is client-side, the best coverage is browser automation:
- **Playwright** (preferred if present under `test-automation/`) or equivalent.

Test cases mapped to AC:
1. **Required field validation**: leaving required fields empty shows inline error(s) and does not send request.
2. **Email validation**: invalid email shows inline error; valid email clears error.
3. **Phone validation**:
   - Non-digits → inline error
   - Below min length → inline error
   - Above max length → inline error
   - Boundary values (10 and 15 digits) accepted
4. **No request is sent when invalid**: assert no network call to `/api/quote-enquiries`.
5. **Valid submission sends exactly one request**: rapid double-click shouldn’t create two requests (note: preventing duplicates is formally ENH-003, but AC here requests “exactly one request” on valid submit; we will ensure the handler doesn’t call fetch more than once per submit event).
6. Preserve existing “Sending…” message state.

If no browser test framework exists, add **minimal JS-unit-like coverage** is not feasible in current stack; fallback to manual test checklist in the plan.

---

## Implementation Tasks (Work Breakdown)

### Task P1 — Update form HTML with error containers (VNK-136)
- **Files:** `dev/app.py`
- Add per-field error `<div>` elements
- Add ids to fields if missing to reliably target them

### Task P2 — Add CSS for error messages and invalid fields (VNK-136)
- **Files:** `dev/app.py`
- Add `.field-error` and `.input-error` styles

### Task P3 — Implement client-side validation functions (VNK-135)
- **Files:** `dev/app.py`
- Add validators for required/email/phone
- Add functions to set/clear inline errors

### Task P4 — Wire validation into submit handler (VNK-135)
- **Files:** `dev/app.py`
- Validate before calling `fetch`
- Focus first invalid field
- Ensure early return prevents request

### Task P5 — Add/Update automated UI tests or manual checklist (VNK-134)
- **Files:** likely under `test-automation/` (if Playwright exists) or `dev/tests/` if there is a UI harness
- Implement the test cases listed above (or add a documented manual checklist if automation not available)

---

## Dependencies
- Confirm existing form field names/ids in `dev/app.py` to correctly map validation and inline errors.
- Test tooling availability:
  - If Playwright exists in `test-automation/`, use it.
  - Otherwise, document a manual QA checklist.

---

## Risks
- Inline landing-page HTML/JS in `dev/app.py` can become hard to maintain; mitigate by keeping changes minimal and well-commented.
- Phone rules may differ from business expectation (exactly 10 digits vs 10–15); keep boundaries centralized in constants for easy adjustment.
- Some browsers already show native validation if `novalidate` is removed; we will keep `novalidate` and rely on custom messaging to meet AC.

---

## Implementation Sequence
1. P1: Add error placeholders near fields
2. P2: Add CSS for errors
3. P3: Add validation helpers
4. P4: Integrate into submit handler + ensure no fetch on invalid
5. P5: Add automation tests (or manual checklist)

---

## Definition of Done
- All AC in VNK-134 are met:
  - Required fields block submission with inline messages
  - Email validation works for valid/invalid
  - Phone digits and length validation includes boundary cases
  - When invalid, **no request** is sent
  - When valid, exactly **one** request is sent and existing “Sending…” behavior remains
- No backend/API changes introduced.
- Tests added/updated and passing (or manual checklist documented if automation unavailable).
- Only planning artifacts committed in this branch.
