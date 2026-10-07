# Requirements - VNK-98: INR currency alignment for payments and invoices

Source: user-story.md (Jira VNK-98, parent VNK-10, enhancement ID VNK-VNK-3-ENH-002). Items not in the story are marked `Not Specified`. Code observations are context only and are not requirements.

## Problem Statement
The payment charge is sent with currency "USD" while the invoice shows the rupee symbol, so currency handling is inconsistent end to end. This risks accounting and payment inconsistencies and shows customers the wrong currency. The story asks to standardize on INR: charge in INR and use INR consistently in order and invoice formatting.

### Current-state observations (from code, informational)
- `dev/services/order_service.py` calls `payment_provider.charge(int(total_amount * 100), 'USD', ...)`. The amount is passed in minor units (x100) and the currency is hardcoded.
- The payment contract (`dev/payments/interface.py`, `PaymentProvider.charge(amount_cents, currency, source, idempotency_key)`) takes `amount_cents`. The only implementation is `dev/payments/mock.py`, which always succeeds.
- Invoice PDFs (`dev/services/invoice.py`, `dev/app/services/pdf_worker.py`) hardcode the "₹" prefix. `dev/templates/invoice_template.html` has no currency symbol or code.
- `dev/app/services/order_service.py` does not call a payment adapter. `dev/app/services/payment_adapter.py` already defaults `currency="INR"` for `create_session`. The story names only `dev/services/order_service.py`, so whether the second path is in scope is unclear (see OQ-08).
- `dev/validation.py` has no currency check, and no currency configuration setting was found.
- The success path in `dev/services/order_service.py` sets `order_status='PROCESSING'` and `payment_status='SUCCESS'`. It does not set "PAID".

## Stakeholders
| Stakeholder | Interest |
|---|---|
| Customer | Pays in, and receives an invoice showing, the correct currency (INR) |
| Admin / accounting | Reconciles payments against orders and invoices with consistent currency |
| Reporter: SONAM BAVISETTI | Story owner |
| Assignee | Not Specified (Unassigned) |
| Parent VNK-10 owner | Not Specified |

## Functional Requirements
- **FR-01**: When the system sends a charge request to the payment adapter for an order, the currency passed must be "INR".
- **FR-02**: The charged amount must equal the order total, expressed in minor units where applicable under the existing adapter contract.
- **FR-03**: The generated invoice must show INR-consistent currency: the symbol "₹" and/or the code "INR".
- **FR-04**: No part of the generated invoice may show "USD".
- **FR-05**: Order creation must be unaffected on the success path. When payment succeeds, the order status remains "PAID" (or the existing success status) and invoice generation completes successfully.
- **FR-06**: If the application is misconfigured with an unsupported currency code and an order is submitted, the API must respond with a validation/config error.
- **FR-07**: In the FR-06 case, no order is created.
- **FR-08**: In the FR-06 case, inventory is not decremented.
- **FR-09**: Order and invoice formatting must use INR consistently (from the proposed improvement). The specific order surfaces are Not Specified (see OQ-07).

## Non-Functional Requirements
- **NFR-01 (Consistency)**: Currency must be consistent across the payment charge, order, and invoice. No mixed USD/INR representation.
- **NFR-02 (Backward compatibility)**: There must be no regression in existing order creation and invoice generation behavior (FR-05).
- **NFR-03 (Data integrity)**: A currency misconfiguration must not leave partial state (no order record, no inventory change).
- **NFR-04 (Testability)**: Each BDD scenario must be verifiable with automated tests, including the currency value received by the adapter.
- NFR for performance, security, audit/logging, and localization: Not Specified.

## Acceptance Criteria
Taken from the story (BDD).

**AC-1 Charge uses INR** (FR-01, FR-02)
- Given an order is submitted with valid items and totals
- When the system sends the charge request to the payment adapter
- Then the currency passed to the adapter is "INR"
- And the charged amount equals the order total in minor units if applicable (per existing adapter contract)

**AC-2 Invoice displays INR consistently** (FR-03, FR-04)
- Given an order is successfully created and an invoice PDF is generated
- When the invoice is rendered
- Then the currency symbol and/or code shown is INR-consistent (₹ and/or "INR")
- And no part of the invoice shows "USD"

**AC-3 Regression, order creation unaffected** (FR-05)
- Given an order is submitted with valid items
- When payment succeeds
- Then the order status remains "PAID" (or the existing success status)
- And invoice generation completes successfully

**AC-4 Negative, invalid currency configuration** (FR-06, FR-07, FR-08)
- Given the application is misconfigured with an unsupported currency code
- When an order is submitted
- Then the API responds with a validation/config error
- And no order is created
- And inventory is not decremented

## Out of Scope
- Real payment gateway integration (separate enhancement ENH-012), per the story.
- Anything not in the story, including multi-currency support, currency conversion, and exchange rates, is not part of this work. These are Not Specified and are treated as out of scope (see Assumption A-01).

## Open Questions / Assumptions
The user has not answered these. Each has a labelled working assumption, which is not a decision. The assumptions need confirmation.

| ID | Gap in the story | Question | Labelled assumption (unconfirmed) |
|---|---|---|---|
| OQ-01 | Where the currency is configured, and which codes are supported: Not Specified | Is currency an env var, a config file, or a constant? Is INR the only supported code? | A-01: A single configured currency value exists, and "INR" is the only supported value. Any other value is "unsupported" for AC-4. The configuration mechanism is Not Specified and is left to design. |
| OQ-02 | Status code and message for the unsupported-currency error: Not Specified. The story says only "validation/config error". | Which HTTP status (400, 422, or 500) and which message or error code? A misconfiguration is arguably a server-side error. | A-02: The error follows the existing error shape (`{'error': <message>}`). The status is Not Specified. The existing order endpoint returns 400 for `ValueError`. |
| OQ-03 | "Minor units if applicable (per existing adapter contract)" | Is the existing contract `amount_cents` (x100) correct for INR (paise)? | A-03: The existing contract is unchanged. The amount is the order total x100 as an integer, now labelled as paise for INR. |
| OQ-04 | Invoice format: "₹ and/or INR" | Must the invoice show the symbol, the code, or both? Where (line items, totals, header)? | A-04: The existing "₹" is kept on all amounts, and "INR" may be added. Either satisfies AC-2 provided "USD" never appears. |
| OQ-05 | Existing USD orders and invoices: Not Specified | Are historical orders or invoices (including PDFs already in `storage/invoices/`) migrated or regenerated? | A-05: Only new charges and newly generated invoices are affected. No back-fill or regeneration is assumed. |
| OQ-06 | Payment adapter file path: Not Specified ("payments layer (adapter)") | Which file is the adapter? | A-06: The adapter is `dev/payments/interface.py` and `dev/payments/mock.py`. `dev/app/services/payment_adapter.py` is a possible second adapter. This is unconfirmed. |
| OQ-07 | "Order/invoice formatting uses INR": which order surfaces? | Do API responses, the order record, or any currency field need to change? Should orders store a currency field? | A-07: No new data field is required. Only the charge currency and invoice rendering change. |
| OQ-08 | `dev/app/services/order_service.py` (the second order path) | Is it in scope? It does not currently call a payment adapter. | A-08: Only `dev/services/order_service.py` is in scope, per the story's affected components. The `dev/app` path is excluded unless confirmed. |
| OQ-09 | Success status wording: the story says "PAID (or existing success status)". The code uses `order_status='PROCESSING'` and `payment_status='SUCCESS'`. | Which value is the baseline for the regression check? | A-09: The existing success status values are the baseline and are unchanged. |
| OQ-10 | Invoice code paths: invoices are generated by `dev/services/invoice.py` and `dev/app/services/pdf_worker.py`, and an HTML template exists. | Which are in scope for FR-03 and FR-04? | A-10: All invoice renderers that show amounts are in scope. This is unconfirmed. |
| OQ-11 | Timing of the currency check (AC-4) | Should the currency be validated before any DB writes or inventory change? In `dev/services/order_service.py`, inventory is decremented before the charge. | A-11: Validation occurs before any order is created or inventory is decremented, as AC-4 requires. How this is done is left to design. |
