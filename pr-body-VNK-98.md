# [VNK-98] INR currency alignment for payments and invoices

Base: main
Head: feature/VNK-98-inr-currency

## Summary
Payments were charged with a hard-coded `'USD'` while invoices displayed rupee amounts. This change charges in INR (configurable via `ORDER_CURRENCY`, default `INR`) and labels both invoice PDF renderers with INR. The rupee glyph does not render in Helvetica, so amounts are prefixed with `INR `.

## Changes
- `dev/services/currency.py` (new): `get_order_currency()` reads `ORDER_CURRENCY` (trimmed, strict exact `INR`), raises `CurrencyConfigError` otherwise; `INVOICE_CURRENCY_LABEL`.
- `dev/services/order_service.py`: charge uses the configured currency instead of `'USD'`.
- `dev/api/orders.py`: unsupported currency configuration returns HTTP 500 with a generic message (status in one constant, `CURRENCY_CONFIG_ERROR_STATUS`).
- `dev/services/invoice.py` and `dev/app/services/pdf_worker.py`: `Currency: INR` line, INR column headers, `INR ` amount prefix.
- Tests: `dev/tests/test_currency.py`, `test_order_currency.py`, `test_orders_currency_api.py`, `test_invoice_inr.py`, `vnk98_support.py`; Playwright `test-automation/tests/vnk98-inr-currency.spec.ts`.
- SDLC docs at repo root (user-story, requirements, architecture, design-review, impl-plan, review) now hold VNK-98 content.

## Verification
- 27 new pytest tests pass (test_currency 12, test_order_currency 8, test_orders_currency_api 4, test_invoice_inr 3).
- New Playwright spec `vnk98-inr-currency.spec.ts`: 1 test passes.
- Full `dev/tests`: 71 passed, 5 failed, 6 errors. The same 11 failures/errors occur on a git-archive of HEAD (dev.app module/package shadowing, admin auth 401s, cart fixture), so no regression was introduced.
- Playwright, all specs, `--workers=1` against a temp-DB server: 22 passed, 15 failed. Causes: vinayaka-checkout expects "Invoice for order <id>" text that HEAD's invoice.py never printed; 5 vnk3 tests need a seeded VFW-1001; 9 vnk134 tests time out on a form field. These 15 were NOT proven pre-existing against a HEAD server; the Playwright baseline was not a true pre-change run.
- `pypdf` was not installed (pip denied), so PDF tests disable page compression and read raw text operands. `requirements.txt` is unchanged.
- Code review (review.md): no Critical/High/Medium findings; Low items F-02..F-06.

## Related issues/tickets
- Jira VNK-98

## Reviewer notes
Unconfirmed assumptions needing a decision:
- D-03: `pdf_worker.py` included as a renderer only.
- D-04: HTTP 500 for unsupported currency (a `ValueError` subclass giving 400 is a one-line alternative).
- D-05: `ORDER_CURRENCY` strict exact `INR` after trim.

Not addressed: charge inside the open transaction (ENH-012); historical USD orders/PDFs untouched; no stored currency column.

Note: this branch was cut from a HEAD where unrelated VNK-2 work was staged; only VNK-98 paths are in this commit.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
