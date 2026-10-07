# Code Review - VNK-98: INR currency alignment for payments and invoices

Scope: `dev/services/currency.py` (new), `dev/services/order_service.py`, `dev/api/orders.py`, `dev/services/invoice.py`, `dev/app/services/pdf_worker.py` (currency-related diffs only). VNK-2 work in the tree is out of scope. The VNK-2 review is backed up in `backups/pre-VNK-98_20261007-122226/`. Review was static (git diff plus a `py_compile` syntax check); no tests were run and no database was touched.

## 1. Summary

The implementation matches the plan (TASK-02 to TASK-06). The charge currency now comes only from a server-side, validated setting. The hardcoded `'USD'` is gone, and no `USD` literal remains in non-test `dev/` code. The currency lookup is the first statement in `create_order`, before payload validation and before `SessionLocal()`, so a bad config fails closed with no DB write. The API maps the error to a generic 500. Both renderers show an explicit INR label. No blockers or major issues. No code changes were needed, and no fixes were applied.

## 2. Findings

| ID | Severity | File | Finding | Action |
|---|---|---|---|---|
| F-01 | Info | `dev/services/currency.py` | Offending env value is logged server-side with `%r` (repr escapes control characters, so no log injection). Required by plan TASK-02; the value is not in the exception or the HTTP response. | None |
| F-02 | Low | `dev/services/currency.py` | `SUPPORTED_CURRENCIES`, `DEFAULT_CURRENCY` and `INVOICE_CURRENCY_LABEL` are separate constants. If a second currency is ever added, the label constant would need to be made per-order. Fine for the INR-only scope. | Note |
| F-03 | Low | `dev/api/orders.py` | `CurrencyConfigError` is caught before `ValueError`. They are unrelated classes, so the order is harmless, and the status is defined once (`CURRENCY_CONFIG_ERROR_STATUS`). The 500 is an unconfirmed assumption (D-04). | Owner to confirm |
| F-04 | Low | `dev/api/orders.py` | `request.json or {}` (pre-existing) raises on non-JSON bodies. Not VNK-98. | Out of scope |
| F-05 | Low | `dev/services/invoice.py`, `pdf_worker.py` | Invoice amounts are now `INR 123.00` and the `₹` glyph is removed (known item: Helvetica lacks U+20B9). The Flask header row is at y=712 and the FastAPI one at y=726. Neither collides with the column headings (680 and 700). Layout is acceptable. | None |
| F-06 | Low | `dev/app/services/pdf_worker.py` | Imports `dev.services.currency` across the `dev/app` boundary (known item, D-03). The module has no side effects or DB access, so the coupling is minimal. | Owner to confirm D-03 |
| F-07 | Info | `dev/services/order_service.py` | Charge runs inside the open transaction after the inventory decrement, and `int(total*100)` truncates. Known item, deferred to ENH-012 (D-07). | Deferred |
| F-08 | Info | repo | `dev.db` shows as modified with an unidentified writer (known item). It was not opened or edited by this review. | User to investigate |
| F-09 | Info | repo | `__pycache__` directories were updated by the `py_compile` run. They are untracked build artefacts. | None |

No Critical, High or Medium findings.

## 3. Auto-fixed items

None. No file was edited other than this report. Nothing was staged, committed or pushed.

## 4. Manual actions required

1. Confirm the unconfirmed assumptions: D-03 (pdf_worker.py in scope), D-04 (500 for a bad config), D-05 (strict `INR` match, unset defaults to INR).
2. Investigate what is modifying `dev.db` (tracked file). Do not commit it with VNK-98.
3. When committing, stage only the five VNK-98 files plus the new tests. The tree also holds staged VNK-2 work on `feature/VNK-2-product-search`; consider a separate branch for VNK-98.
4. The verify phase must write the tests (TASK-07 to TASK-09) using a temp `DATABASE_URL` set before importing `dev.db`. The existing tests call `init_db()` against the default `dev.db`.
5. Optionally check visually that the generated PDFs look right with the `INR ` prefix (the D-02 manual check).
6. Remove the generated `storage/invoices/` files before commit (untracked).

## 5. Plan conformance

| Item | Result |
|---|---|
| TASK-02 currency module: constants, `CurrencyConfigError(Exception)` (not `ValueError`), call-time env read, trim, unset gives INR, empty, whitespace, `inr` and `USD` raise, generic message, no import side effects | Conforms |
| TASK-03 `get_order_currency()` is the first statement, before `validate_order_payload` and `SessionLocal()`; charge uses `currency`; amount, idempotency key and statuses unchanged; payload `currency` ignored | Conforms |
| TASK-04 `except CurrencyConfigError` returns the exact message with a single status constant; `ValueError` gives 400 unchanged; value not echoed | Conforms |
| TASK-05 Flask renderer: "Currency: INR" header, "Price (INR)" and "Total (INR)" headings, `INR ` amount prefix, no template change | Conforms |
| TASK-06 FastAPI renderer: same labelling, only `pdf_worker.py` changed in `dev/app/` | Conforms |
| `dev/payments/`, `dev/templates/`, `dev.db`, `alembic*` | Not touched by VNK-98 diffs |

Requirement coverage by code:
- FR-01, FR-02 (charge currency INR, from server config only): met.
- FR-03, FR-04, FR-09 (invoice labelling in both renderers): met.
- FR-05, FR-07, FR-08 (success statuses and amount unchanged, payload `currency` ignored): met.
- FR-06 (fail-closed error): met.
- AC-1: met in code. AC-2: met in code. AC-3: unchanged success path. AC-4: met in code.
- AC-1 to AC-4 are not yet proven by tests; that is the verify phase's job.
- NFR-01 and NFR-03: met. NFR-02 and NFR-04: pending the baseline and regression runs and the new tests.

## 6. Security checklist

| Check | Result |
|---|---|
| Currency sourced only from server config, not from request payload | Pass. `payload` is never read for currency. |
| Allow-list validation (exact `INR`) | Pass. |
| Configured value not echoed in the HTTP response or exception | Pass. Generic message. |
| Value logged server-side safely | Pass. `%r` escaping; no secrets involved. |
| Fail-closed on a bad or empty config | Pass. Raises; no default fallback for an empty or invalid value. |
| Ordering: failure occurs before any DB write or inventory change or charge | Pass. First statement of `create_order`. |
| Error not swallowed by a broad handler | Pass. No broad `except` in the service or handler. |
| No injection risks in the renderers | Pass. The label is a constant; amounts are formatted floats. |
| No new dependencies or secrets | Pass (runtime). `pypdf` is planned test-only. |
| No `USD` literal left in non-test `dev/` code | Pass (grep). |
| Syntax check of the five files | Pass (`py_compile`). |

Residual risk: the 500 response on a misconfiguration reveals only that the configuration is unsupported. Charge-in-transaction (ENH-012) is accepted.
