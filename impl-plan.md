# Implementation Plan - VNK-98: INR currency alignment for payments and invoices

Inputs: `requirements.md`, `architecture.md`, `design-review.md` (verdict APPROVE, user approved). Supersedes the VNK-2 plan (backup in `backups/pre-VNK-98_20261007-122226/`). Scope is `dev/` and `test-automation/` only. This document contains no application code.

## 1. Summary

Replace the hardcoded `'USD'` charge currency with a validated server-side value (INR), label both invoice renderers explicitly as INR, and prove it with tests. Work is 10 small tasks: baseline, currency module, order service wiring, API error mapping, two renderer edits, a PDF test helper, tests, an E2E check, and a final regression run. No schema change, no migration, no payload `currency` input.

Note on ownership: the verify phase (step 07) owns writing the new tests. Test tasks (TASK-07 to TASK-09) are listed here so that scope, patch points and DoD are fixed, but they are executed in the verify phase, not the implementation phase. Implementation-phase tasks are TASK-02 to TASK-06. TASK-01 (baseline run) and TASK-10 (regression run) only execute existing tests.

### Unconfirmed assumptions settled in this plan
These come from the architecture's proposals. The user did not answer them. They are assumptions, not confirmed decisions, and each needs product-owner confirmation.

| ID | Assumption (UNCONFIRMED) | Plan decision |
|---|---|---|
| D-03 | `dev/app/services/pdf_worker.py` is in scope as an invoice renderer only. | Included (TASK-06). The rest of the FastAPI path (`dev/app/services/order_service.py`, `dev/app/main.py`, `dev/app/api/orders.py`, `payment_adapter.py`) is untouched. Decision record: "Renderer-only inclusion of pdf_worker.py, per A-08/A-10 reconciliation." If the owner wants zero FastAPI changes, drop TASK-06 and its tests; AC-2 is then met for Flask invoices only. |
| D-04 | Unsupported currency returns HTTP 500 `{'error': 'unsupported currency configuration'}`. | `CurrencyConfigError` derives from `Exception`, not `ValueError`. Noted alternative: a `ValueError` subclass gives 400 with no handler change. Tests assert one status constant, so a switch is a one-line change. |
| D-05 | Env var `ORDER_CURRENCY`; strict exact `INR` after trimming whitespace; unset defaults to `INR`; empty string (or whitespace only) raises; lower-case `inr` raises. | Adopted as written. Read at call time, not import time. |

### Items settled by the plan (no user input needed)
- **D-01 (PDF text extraction):** ReportLab content streams are compressed, so byte grep proves nothing. Decision: use the `pypdf` library as a test-only dependency (`PdfReader(...).pages[i].extract_text()`), added to `requirements.txt` in TASK-07 (a comment marks it test-only). Fallback if the owner rejects a new dependency: in the test only, build the PDF with stream compression off (ReportLab `pageCompression=0` / `rl_config.pageCompression = 0` set via monkeypatch) and search raw bytes. Production renderer code does not change for this. The architecture's "no new libraries" statement is corrected: no new runtime library; one test-only library. Note that text extraction of WinAnsi Helvetica text returns "INR"; a missing `₹` glyph will not appear in extracted text, which is why INR is the asserted token.
- **D-02 (invoice symbol):** Always print the explicit ASCII label "INR" (header line "Currency: INR", column headings "Price (INR)" and "Total (INR)"). The `₹` symbol is optional and is not asserted by any test and not a runtime branch. Decision: keep the existing `₹` text on amounts untouched only if it does not break rendering; otherwise leave as is. No font embedding. Because built-in Helvetica has no U+20B9 glyph, a one-time manual check (TASK-04) records whether `₹` renders. If it does not, amounts are prefixed "INR " in place of `₹` as a fixed, unconditional change in the source, not a branch on environment. That one-time result is written in the task notes only.
- **D-06 (spy patch point):** `payment_provider` is a module-level object in `dev/services/order_service.py` (`payment_provider = MockPayment()`, line 9). Patch point: `monkeypatch.setattr(dev.services.order_service, "payment_provider", spy)` where the spy exposes `charge(amount_cents, currency, source, idempotency_key)`, records its arguments and returns an object with `.success = True` (mirroring MockPayment's return shape; the test author must confirm the shape in `dev/payments/mock.py`). Patch the name in `order_service`, not in `dev.payments.mock`. AC-4 is covered in pytest (env set via `monkeypatch.setenv("ORDER_CURRENCY", "USD")`), not in Playwright, because Playwright would need a second server with a bad environment.
- **Success status:** code writes `order_status='PROCESSING'` and `payment_status='SUCCESS'`. The literal "PAID" is never produced. Tests assert `PROCESSING` and `SUCCESS`; a test expecting "PAID" is a wrong test (A-09).

## 2. WARNING: database safety

Existing tests and specs call `init_db()` against the default `sqlite:///dev.db` (for example `dev/tests/test_app_order_service.py` and `dev/tests/test_pdf_worker.py`; `dev/db.py` reads `DATABASE_URL` at import time with default `sqlite:///dev.db`). **`dev.db` must not be touched by any task in this plan.**
- Set `DATABASE_URL` to a temp file (for example `sqlite:///<tmp>/vnk98.db`) in the environment before starting pytest, and before any `dev.db` module import (the engine is built at import time, so `monkeypatch.setenv` inside a test is too late unless the module is reloaded, as `test_cart_api.py` and `test_quote_enquiries.py` do).
- Same for the Flask server used by Playwright: start it with a temp `DATABASE_URL`.
- Baseline (TASK-01) and regression (TASK-10) runs must use the temp `DATABASE_URL` too. Confirm `dev.db` modification time and size are unchanged before and after (check with `git status`/file stat; do not open it).
- Tests that write invoice PDFs should use a temp invoice directory where the code allows; otherwise note any files created under `storage/invoices/` and do not commit them.

## 3. Task breakdown

### TASK-01: Baseline test run (no code change)
- Description: With a temp `DATABASE_URL` set, run the existing pytest suite (`dev/tests/`) and record pass/fail per test, including any pre-existing failures, as the regression reference. Run the Playwright specs only if a server with a temp DB is available; otherwise record them as not run.
- Target files: none modified (read-only). Results recorded in the task report.
- Depends on: none.
- Satisfies: NFR-02, NFR-04 (baseline for FR-05/AC-3).
- DoD: Baseline pass/fail list recorded. `dev.db` untouched (verified). Pre-existing failures are labelled as such so they are not blamed on VNK-98. No files changed.

### TASK-02: Currency policy module
- Description: Create `dev/services/currency.py` containing `SUPPORTED_CURRENCIES = frozenset({"INR"})`, `CurrencyConfigError(Exception)`, and `get_order_currency()` that reads `ORDER_CURRENCY` at call time, trims whitespace, returns `"INR"` when unset, and raises `CurrencyConfigError` for empty, whitespace-only, lower-case or any other value. Log the offending value server-side only; the exception message is generic. Optionally a fixed `INVOICE_CURRENCY_LABEL = "INR"` constant, so renderers share one source. Import-time side effects: none.
- Target files: `dev/services/currency.py` (new).
- Depends on: TASK-01.
- Satisfies: FR-01, FR-06, NFR-01, NFR-03; D-05; ADR-01.
- DoD: Unset -> `INR`; `" INR "` -> `INR`; `USD`, `inr`, empty, whitespace -> `CurrencyConfigError`. The exception is not a `ValueError` subclass. The module imports without environment variables set and with no DB access.

### TASK-03: Wire the currency into create_order
- Description: In `create_order`, call `get_order_currency()` as the first statement, before `validate_order_payload` and before `SessionLocal()`. Replace the hardcoded `'USD'` argument in `payment_provider.charge(...)` with the returned value. Keep the amount `int(total_amount * 100)`, the idempotency key and the success statuses unchanged. Ignore any `currency` key in the payload.
- Target files: `dev/services/order_service.py`.
- Depends on: TASK-02.
- Satisfies: FR-01, FR-02, FR-05, FR-07, FR-08, NFR-01, NFR-03; AC-1, AC-3, AC-4 (service level); ADR-03, ADR-04.
- DoD: No `'USD'` literal remains in `dev/services/order_service.py`. The currency lookup precedes any DB access. Statuses `PROCESSING`/`SUCCESS` unchanged. `dev/payments/` untouched. Existing order tests still pass under a temp DB.

### TASK-04: Map CurrencyConfigError in the orders API
- Description: In the `POST /api/orders` handler add an `except CurrencyConfigError` branch returning `{'error': 'unsupported currency configuration'}` with status 500 (D-04, unconfirmed). Place it so that it does not get swallowed by a broader `except Exception` that may already exist, and keep the `ValueError` -> 400 mapping unchanged. Do not echo the configured value.
- Target files: `dev/api/orders.py`.
- Depends on: TASK-02, TASK-03.
- Satisfies: FR-06, NFR-03; AC-4; ADR-02.
- DoD: With `ORDER_CURRENCY=USD`, the endpoint returns 500 with the exact message above; with valid config it returns 201 as before; `ValueError` still gives 400. The status is defined once (a single constant or literal) so switching to 400 is a one-line change.

### TASK-05: Flask invoice renderer INR label
- Description: In `generate_invoice` add a "Currency: INR" header line and "(INR)" in the Price and Total column headings. Keep the existing amount formatting; apply the one-time D-02 manual check on whether `₹` renders in the generated PDF and, if it does not, replace the `₹` prefix with "INR " unconditionally. No "USD" text anywhere. No template change (`dev/templates/invoice_template.html` stays out of scope).
- Target files: `dev/services/invoice.py`.
- Depends on: TASK-02 (shared label constant, if used), TASK-03 not required.
- Satisfies: FR-03, FR-04, FR-09, NFR-01; AC-2; ADR-05; D-02.
- DoD: Generated PDF text (via pypdf, see TASK-07) contains "INR" and not "USD". The invoice row still reaches `READY`. The D-02 check result is noted in the task report.

### TASK-06: FastAPI invoice renderer INR label (renderer only; D-03 assumption)
- Description: Same labelling as TASK-05 in `generate_invoice_pdf`. No change to any other file in `dev/app/`.
- Target files: `dev/app/services/pdf_worker.py`.
- Depends on: TASK-05 (consistent wording).
- Satisfies: FR-03, FR-04, FR-09, NFR-01; AC-2; ADR-05; D-03 (unconfirmed).
- DoD: Generated PDF text contains "INR" and not "USD". `dev/app/services/order_service.py`, `main.py`, `api/orders.py`, `payment_adapter.py` unchanged (check `git diff`). Existing `dev/tests/test_pdf_worker.py` passes under a temp DB. Skippable if the owner rejects D-03.

### TASK-07: Test support and unit/service tests (verify phase owns writing)
- Description: Add `pypdf` as a test-only dependency (D-01) with a small test helper that extracts all page text from a PDF. Write pytest tests: (a) `get_order_currency` unit cases (unset, `INR`, padded, `USD`, `inr`, empty, whitespace); (b) service-level AC-1 using the D-06 spy at `dev.services.order_service.payment_provider`, asserting `currency == "INR"` and `amount == int(total * 100)`; (c) AC-4 service negative: `ORDER_CURRENCY=USD`, assert `CurrencyConfigError`, zero rows in customers/orders/order_items/invoices, product `quantity_available` unchanged, spy not called; (d) AC-3 success path asserts `PROCESSING` and `SUCCESS` (never "PAID") and invoice `READY`; (e) AC-2 for both renderers: "INR" present and "USD" absent. All with temp `DATABASE_URL`, reloading `dev.db` as the cart/quote tests do, if setting the env after import.
- Target files: `requirements.txt` (add `pypdf`, test-only comment), `dev/tests/test_currency.py` (new), `dev/tests/test_order_currency.py` (new), `dev/tests/test_invoice_inr.py` (new).
- Depends on: TASK-03, TASK-04, TASK-05, TASK-06.
- Satisfies: NFR-04; FR-01..FR-08; AC-1, AC-2, AC-3, AC-4; D-01, D-05, D-06.
- DoD: New tests pass; each AC maps to at least one test; no test touches `dev.db`; no test expects "PAID"; spy approach verified to fail if `'USD'` is reintroduced.

### TASK-08: API-level tests (verify phase owns writing)
- Description: With the Flask test client: misconfigured env returns the chosen status (500) and the exact error body, with no order created and inventory unchanged (AC-4); valid env returns 201 and `GET /api/orders/<id>` shows `PROCESSING` (AC-3); a payload containing `currency: "USD"` is ignored and the charge still uses INR (spy).
- Target files: `dev/tests/test_orders_currency_api.py` (new).
- Depends on: TASK-07.
- Satisfies: FR-05, FR-06, FR-07, FR-08, NFR-03, NFR-04; AC-3, AC-4; D-04.
- DoD: Tests pass under a temp `DATABASE_URL`; the status code is asserted through one constant, so a D-04 change updates one place.

### TASK-09: Playwright end-to-end check (verify phase owns writing)
- Description: Via the API, place a valid order, fetch the invoice and assert INR is present and "USD" absent (text extracted from the PDF using the test runner's available means, or by calling the server's invoice endpoint and checking the response), and that the order status is `PROCESSING`. AC-4 is not covered here (needs a second server with a bad env var; covered in pytest per D-06). The server under test must use a temp `DATABASE_URL`.
- Target files: `test-automation/tests/vnk98-inr-currency.spec.ts` (new).
- Depends on: TASK-05, TASK-07.
- Satisfies: NFR-04; AC-2, AC-3.
- DoD: Spec passes against a server started with a temp DB; no changes to existing specs.

### TASK-10: Regression run (final)
- Description: Re-run the full pytest suite and, where a server is available, the Playwright specs, with a temp `DATABASE_URL`. Compare to the TASK-01 baseline.
- Target files: none modified.
- Depends on: TASK-01 to TASK-09.
- Satisfies: NFR-02, FR-05; AC-3.
- DoD: No test that passed at baseline now fails; new tests pass; `git diff` shows changes only in the files listed in this plan; `dev.db` unchanged; nothing staged, committed or pushed by this plan's tasks unless the user asks.

## 4. Execution order

1. TASK-01 baseline.
2. TASK-02 currency module (foundation; no dependencies on the other code).
3. TASK-03 order service, then TASK-04 API mapping (TASK-04 needs the exception and the raise site).
4. TASK-05 Flask renderer, then TASK-06 FastAPI renderer. These are independent of TASK-03/04 and can run in parallel with them after TASK-02.
5. TASK-07, TASK-08, TASK-09 in the verify phase (tests; 07 first because it adds the extractor and helpers).
6. TASK-10 regression last.

Rationale: baseline first so regressions are attributable; the policy module before its callers; renderers are independent leaf edits; tests last because they need all behaviour in place and are owned by the verify phase.

## 5. Traceability matrix

| Requirement | Tasks |
|---|---|
| FR-01 | TASK-02, 03, 07 |
| FR-02 | TASK-03, 07 |
| FR-03 | TASK-05, 06, 07 |
| FR-04 | TASK-05, 06, 07 |
| FR-05 | TASK-03, 07, 08, 10 |
| FR-06 | TASK-02, 04, 08 |
| FR-07 | TASK-03, 07, 08 |
| FR-08 | TASK-03, 07, 08 |
| FR-09 | TASK-05, 06 |
| NFR-01 | TASK-02, 03, 05, 06 |
| NFR-02 | TASK-01, 10 |
| NFR-03 | TASK-02, 03, 04, 08 |
| NFR-04 | TASK-07, 08, 09 |
| AC-1 | TASK-03, 07 |
| AC-2 | TASK-05, 06, 07, 09 |
| AC-3 | TASK-03, 07, 08, 09, 10 |
| AC-4 | TASK-03, 04, 07, 08 |

## 6. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Tests or runs touch the default `dev.db` through `init_db()` | High | High | Section 2: temp `DATABASE_URL` set before import, stat check of `dev.db` before and after. |
| R-02 | `₹` does not render in Helvetica; invoice looks wrong | Medium | Medium | Explicit "INR" label always printed (D-02); one-time check; unconditional "INR " prefix if needed. |
| R-03 | PDF text extraction fails on compressed streams (D-01) | Medium | Medium | `pypdf` as test-only dependency; fallback is disabling page compression in the test. |
| R-04 | Owner rejects an unconfirmed assumption (D-03, D-04, D-05) | Medium | Low | Each is isolated: drop TASK-06; change one status constant; change one validation rule. |
| R-05 | Spy shape differs from `MockPayment` return, causing false failures | Low | Medium | Mirror the real return shape; verify in `dev/payments/mock.py` while writing TASK-07. |
| R-06 | Test expects "PAID" and fails | Medium | Low | Assert `PROCESSING`/`SUCCESS` per A-09; document in tests. |
| R-07 | `dev.db` engine is built at import time, so env set in a test is ignored | Medium | High | Set env before import or reload the module as `test_cart_api.py` does. |
| R-08 | A broad `except Exception` in the orders API hides `CurrencyConfigError` or maps it wrongly | Low | Medium | TASK-04 places the branch first; API test in TASK-08. |
| R-09 | Invoice PDFs written to `storage/invoices/` during tests pollute the repo | Medium | Low | Use a temp directory where possible; do not commit generated files. |
| R-10 | Latent issues (charge in open transaction, `int(total*100)` truncation) | Low | Medium | Accepted (D-07); deferred to ENH-012. |
