# Architecture - VNK-98: INR currency alignment for payments and invoices

Inputs: requirements.md (VNK-98, OQ-01..OQ-11 unanswered, assumptions A-01..A-11 unconfirmed). Scope is a small, targeted change to the existing Flask `dev/` stack. No new feature, no schema change, no new dependency.

## 1. Overview

Today the charge is hardcoded to `'USD'` in `dev/services/order_service.py` while both invoice renderers print "₹". The design introduces one tiny currency module as the single place where the order currency is read and validated, passes that value to the payment adapter, and labels the invoice renderers explicitly as INR.

Key points:
- The currency is validated first in `create_order`, before the session is opened. A misconfigured currency therefore cannot create an order, a customer, or change inventory (AC-4).
- The adapter contract (`amount_cents`, x100) is unchanged. For INR the same integer is paise.
- Success status values stay `order_status='PROCESSING'`, `payment_status='SUCCESS'`. The literal "PAID" is not produced by the code and is not introduced (A-09).
- Out of scope: the FastAPI path under `dev/app/`, real gateway (ENH-012), multi-currency, conversion, back-fill of old invoices.

## 2. Scope decision (OQ-08, OQ-06, OQ-10)

| Path | Stack | Decision | Reason |
|---|---|---|---|
| `dev/api/orders.py` -> `dev/services/order_service.py` | Flask | IN | The story's named component; the only order path that calls a charge with a currency. |
| `dev/payments/interface.py`, `mock.py` | Flask path | IN (no code change expected) | Contract already takes `currency`. The mock ignores it. Only the caller changes. See ADR-04. |
| `dev/services/invoice.py` | Flask path | IN | Hardcodes "₹"; called by `create_order`. Needs explicit INR label. |
| `dev/app/services/pdf_worker.py` | FastAPI path | IN (renderer only) | Same "₹" hardcoding and FR-03/FR-04 apply to every invoice renderer that shows amounts (A-10). It is a pure rendering change with no order-flow coupling. |
| `dev/app/services/order_service.py`, `dev/app/main.py`, `dev/app/api/orders.py` | FastAPI | OUT | Does not call any payment adapter, so there is no USD charge to fix and no ordering problem to solve. Adding a currency check there would be new behavior beyond the story (A-08). |
| `dev/app/services/payment_adapter.py` | FastAPI | OUT, no change | Already defaults `currency="INR"`, which is consistent. Left as is. |
| `dev/templates/invoice_template.html` | n/a | OUT | No code references it (grep found no loader); it has no currency symbol and no "USD". Not rendered, so FR-04 cannot be violated through it. Revisit only if a renderer starts using it. |

Note on A-08 vs A-10: A-08 excludes the `dev/app` order path, A-10 includes all invoice renderers. These are compatible: `pdf_worker.py` is included as a renderer only. This partial inclusion is a judgement call; see Section 11.

## 3. Component diagram

```
 Client
   | POST /api/orders
   v
 dev/api/orders.py  (Flask blueprint)
   |  maps CurrencyConfigError -> 500 {'error': ...}
   |  maps ValueError          -> 400 {'error': ...}   (unchanged)
   v
 dev/services/order_service.py :: create_order(payload)
   |  1. get_order_currency()  <---- dev/services/currency.py  (NEW)
   |        reads env ORDER_CURRENCY (default "INR"), validates against {"INR"}
   |        raises CurrencyConfigError on failure
   |  2. validate_order_payload(payload)       (unchanged)
   |  3. open session; customer, order, items, inventory decrement (unchanged)
   |  4. payment_provider.charge(int(total*100), currency, source, key)
   |        dev/payments/interface.py + mock.py (unchanged)
   |  5. on success: PROCESSING / SUCCESS, Invoice row, commit
   |  6. dev/services/invoice.py :: generate_invoice  (INR label added)
   v
 storage/invoices/invoice_<id>.pdf

 Separate (FastAPI): dev/app/services/pdf_worker.py :: generate_invoice_pdf  (INR label added; not on the Flask order path)
```

## 4. Components

| Component | File | Change | Responsibility |
|---|---|---|---|
| Currency policy | `dev/services/currency.py` (new) | New | `SUPPORTED_CURRENCIES = frozenset({"INR"})`, `CurrencyConfigError`, `get_order_currency()` and an `INVOICE_CURRENCY_LABEL` helper if needed. Single source of truth for the code. |
| Order service | `dev/services/order_service.py` | Edit | Calls `get_order_currency()` as the first statement of `create_order`; passes the result to `charge()` instead of `'USD'`. |
| Orders API | `dev/api/orders.py` | Edit | Adds an `except CurrencyConfigError` branch returning the existing `{'error': msg}` shape with a 5xx status. |
| Payment contract | `dev/payments/interface.py`, `mock.py` | None | Unchanged. Parameter name `amount_cents` is kept (ADR-04). |
| Flask invoice renderer | `dev/services/invoice.py` | Edit | Adds an explicit "Currency: INR" line and "(INR)" in the Price/Total column headings. Keeps "₹" subject to the glyph check in Section 10. |
| FastAPI invoice renderer | `dev/app/services/pdf_worker.py` | Edit | Same labelling as above. |
| Tests | `dev/tests/` (pytest), `test-automation/` (Playwright/TypeScript) | New | See Section 9. |

## 5. Data model

No change. No migration. No `currency` column on `Order` or `Invoice` (A-07): with INR as the only supported value a stored column would be a constant, and storing it would invite the multi-currency scope the story excludes. Historical rows and PDFs are untouched (A-05).

Configuration (not persisted):
| Key | Source | Default | Valid values |
|---|---|---|---|
| `ORDER_CURRENCY` | environment variable | `INR` when unset | `INR` only |

## 6. API surface

| Endpoint | Change |
|---|---|
| `POST /api/orders` | Success: unchanged, `201 {'status': 'created', 'order_id': ...}`. New failure: when the configured currency is not supported, `500 {'error': 'unsupported currency configuration'}` (see ADR-02, OQ-02). Other errors unchanged (`ValueError` -> 400). |
| `GET /api/orders/<id>` | Unchanged. It returns `status` (e.g. `PROCESSING`) and `total_amount`; no currency field is added (A-07). |
| Invoice download endpoints | Unchanged routes; the PDF content changes. |

## 7. Data flow

Success path:
1. `POST /api/orders` -> `create_order`.
2. `get_order_currency()` returns `"INR"`.
3. Payload validation, customer, order, items, inventory decrement, subtotal and total (unchanged).
4. `charge(int(total * 100), "INR", source, idempotency_key)`; amount is paise.
5. On `pay.success`: `payment_status='SUCCESS'`, `order_status='PROCESSING'`, Invoice row `PENDING`, commit.
6. `generate_invoice(order.id)` writes the PDF with the INR label and sets the invoice to `READY`.
7. API returns 201.

Unsupported currency path (AC-4):
1. `ORDER_CURRENCY=USD` (for example). `get_order_currency()` raises `CurrencyConfigError` at step 2 of the success path, before `SessionLocal()` is opened and before `validate_order_payload`.
2. No Customer, Order, OrderItem, Invoice row, or inventory change exists, because no DB session has been touched. FR-07, FR-08 and NFR-03 hold by construction rather than by rollback.
3. The API returns the error response. The offending value is logged server-side, not returned.

Why ordering rather than rollback: in the current code a `ValueError` after the inventory decrement already rolls back, since `SessionLocal()` is used as a context manager without commit. Relying only on that would work but would also run every write before failing, and would couple correctness to the exception path. A check before any write is cheaper and directly testable (OQ-11, A-11).

## 8. Technology stack

- Python 3, Flask (`dev/api`, `dev/services`), SQLAlchemy, ReportLab (invoice PDFs), pytest for unit and API tests under `dev/tests/`.
- Playwright with TypeScript under `test-automation/` for end-to-end verification.
- No new libraries. Configuration through `os.getenv`, consistent with `dev/db.py` and `dev/api/products.py`.
- `dev/config.py::get_config()` is deliberately not used: it raises when `SECRET_KEY` is absent, which would make an order request fail for an unrelated reason and complicates tests. Extending the `Config` dataclass is rejected for the same reason (ADR-01).

## 9. Testability (NFR-04)

- Unit: `get_order_currency()` returns INR when unset or `INR`; raises for `USD`, empty string, and lower-case `inr` (see Section 11 on normalisation).
- Service: patch `payment_provider` with a spy and assert `charge` is called with `currency == "INR"` and `amount == int(total * 100)` (AC-1).
- Service negative: set the env to `USD`, call `create_order`; assert `CurrencyConfigError`, zero rows in orders, customers and order_items, product `quantity_available` unchanged, and the spy not called (AC-4).
- API: `POST /api/orders` with misconfigured env returns the 5xx error shape; with valid env returns 201 and `GET` shows `PROCESSING` (AC-3).
- PDF: extract text from the generated PDF for both renderers; assert "INR" present and "USD" absent (AC-2).
- Playwright (`test-automation/`): place an order through the API, fetch the invoice, assert the same.

## 10. Security considerations

- The currency comes only from server-side configuration, never from the request payload. A client cannot select the charge currency, which closes a tampering path (e.g. paying 1 unit in a cheaper currency). Any `currency` key in the payload is ignored.
- Error responses do not echo the configured value or environment details; the detail goes to the server log.
- No secrets are involved. `ORDER_CURRENCY` is not sensitive, but it must be changed only through deployment configuration, not any admin endpoint.
- Fail closed: an unsupported value stops order creation rather than falling back to a default, so a typo cannot silently charge in the wrong currency.
- Invoice text uses values from the DB and fixed labels only; no new injection surface.
- Glyph risk (integrity of the invoice, AC-2): the renderers use the built-in ReportLab Helvetica font, which has no U+20B9 glyph. A check while preparing this design showed the PDF bytes do not contain the UTF-8 form of "₹" and no error is raised, so the symbol may render as a blank or wrong character today. Because of this, the explicit ASCII "INR" label is the reliable part of the AC-2 evidence. The implementation must verify how "₹" renders; if it does not render, replace it with the "INR " prefix (still satisfies "₹ and/or INR"). Embedding a TTF font is not proposed, to keep the change minimal.

## 11. Scalability and reliability

- The currency check is an env lookup and a set membership test, negligible cost, with no I/O and no new shared state; it does not affect concurrency or horizontal scaling.
- Reliability: the check precedes all writes (all-or-nothing). Existing failure behaviour is unchanged.
- Existing weakness noted, not fixed (out of scope): inventory is decremented before the charge, and the charge is made inside the open transaction. If `charge` raises a non-`ValueError` exception, the session rolls back, but with a real gateway the charge could succeed externally and a later failure (e.g. the commit) would leave a charge without an order. The mock cannot show this. This should be addressed in ENH-012, not here.
- The idempotency key is passed unchanged; nothing in this change alters retry semantics. Concurrent requests with the same inputs still behave as today.
- Invoice generation happens after commit; a renderer failure leaves a `PENDING` invoice as today. Unchanged.

## 12. ADRs

### ADR-01: Currency configured by a dedicated env var read in a small module
- Status: Proposed (resolves OQ-01, adopts A-01).
- Context: no currency setting exists. `dev/config.py` requires `SECRET_KEY`; other modules use `os.getenv` directly.
- Decision: new `dev/services/currency.py` reads `ORDER_CURRENCY` (default `INR`), validates against `{"INR"}`, and raises `CurrencyConfigError`. Read at call time, not import time, so tests and a misconfiguration can be exercised without reloading modules, and so a bad value cannot crash the whole app at import.
- Alternatives: hardcode `'INR'` in the order service (simplest, but then AC-4 has no way to occur and cannot be tested); extend `get_config()` (coupled to `SECRET_KEY`, and validates at startup which skips the per-request AC-4 behaviour); a constant (same problem as hardcoding).
- Consequences: one more env var; INR is the default so existing deployments need no change.

### ADR-02: Unsupported currency is a server-side error, HTTP 500, not a ValueError
- Status: Proposed (OQ-02; deviates from the weak baseline in A-02).
- Context: the story says "validation/config error". The existing handler maps `ValueError` to 400. A bad server setting is not the client's fault, and a 400 would tell the client to change a request that cannot fix it.
- Decision: `CurrencyConfigError` derives from `Exception`, not `ValueError`, and the Flask handler returns `500 {'error': 'unsupported currency configuration'}`, keeping the existing error shape.
- Alternative: subclass `ValueError` and get 400 with no handler change (zero extra code). Acceptable if the product owner prefers it; the AC wording is satisfied either way. The status code is the only thing to confirm.

### ADR-03: Validate before opening the session
- Status: Proposed (OQ-11, adopts A-11).
- Decision: `get_order_currency()` is the first statement in `create_order`, before `validate_order_payload` and `SessionLocal()`.
- Rationale: no writes exist to undo; the behaviour is testable by asserting the DB is untouched. A configuration fault takes priority over payload errors, so the response is the same regardless of the payload.
- Alternative: validate after payload validation (different error precedence only) or rely on rollback (rejected in Section 7).

### ADR-04: Keep the adapter contract and the `amount_cents` name
- Status: Proposed (OQ-03, OQ-06; adopts A-03, A-06).
- Decision: no change to `PaymentProvider.charge`. Amount stays `int(total_amount * 100)`; for INR this is paise (INR has 2 decimals, so x100 is correct). The mock continues to ignore the currency, so the spy-based test in Section 9 is what proves AC-1.
- Alternative: rename to `amount_minor` (cleaner, but touches the interface, mock and every caller for no behavioural gain; deferred to ENH-012).
- Note: `int(total_amount * 100)` truncates a `Decimal`. Prices with at most 2 decimals are exact, so it is correct for current data; flagged only as a latent concern.

### ADR-05: Label INR explicitly in both invoice renderers, no template change
- Status: Proposed (OQ-04, OQ-10; adopts A-04, A-10).
- Decision: add "Currency: INR" in the header block and "(INR)" in the Price/Total column headings in `invoice.py` and `pdf_worker.py`. Keep "₹" on amounts unless the glyph check (Section 10) shows it does not render, in which case use an "INR " prefix. The unused HTML template is left alone.
- Alternative: embed a Unicode TTF (reliable "₹", but adds a font asset and a code path); rejected as over-scope.

### ADR-06: No stored currency field, no migration
- Status: Proposed (OQ-07, OQ-05; adopts A-07, A-05).
- Decision: do not add `currency` to `Order` or `Invoice`; do not regenerate old PDFs.
- Rationale: INR is the single supported value, and the story's out-of-scope list excludes multi-currency. Add a column only when a second currency is a real requirement.

## 13. Assumption review and open ambiguities

Adopted as written: A-01, A-03, A-04, A-05, A-06, A-07, A-09, A-10, A-11.

Adopted with change or concern:
- A-02 (error status): the architecture proposes 500, not the 400 that the baseline suggests (ADR-02). Needs a product decision, though both satisfy AC-4.
- A-08 (exclude `dev/app`) combined with A-10 (all renderers): treated as "FastAPI order flow out, `pdf_worker.py` renderer in". If the owner wants zero FastAPI changes, drop that one file; AC-2 is then only met for Flask-generated invoices.
- A-06: only `dev/payments/` is a real adapter in the Flask path; `payment_adapter.py` is a Stripe stub that is already INR. No conflict.

Remaining ambiguities for the next phase:
1. Env var name `ORDER_CURRENCY` is a design proposal, not a requirement.
2. Case handling: is `inr` accepted? The design is strict (exact `INR` only, after trimming whitespace) so that behaviour is explicit; confirm.
3. A-09/FR-05 wording: the story says "PAID". The code never writes it. Tests must assert `PROCESSING` and `SUCCESS`; any test expecting "PAID" would fail and be a wrong test, not a regression.
4. "₹" glyph rendering (Section 10) is unverified at the PDF level; it needs a text-extraction or visual check at implementation time.
5. Whether the `dev/app` FastAPI order flow should eventually enforce the same currency is deferred; it has no charge today.
