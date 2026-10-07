# VNK-98: INR currency alignment for payments and invoices

## Metadata
| Field | Value |
|---|---|
| Key | VNK-98 |
| URL | https://sonambavisetti.atlassian.net/browse/VNK-98 |
| Type | Story |
| Status | To Do |
| Priority | Medium |
| Parent | VNK-10 |
| Reporter | SONAM BAVISETTI |
| Assignee | Unassigned |
| Labels / Components / Fix versions | None |
| Created | 2026-09-22 |
| Updated | 2026-09-22 |
| Due date | None |

## Description

### Traceability
- Approved Enhancement ID: VNK-VNK-3-ENH-002
- Original gap: Payment charge uses currency 'USD' while invoice uses ₹; amounts have inconsistent currency handling.
- Proposed improvement: Standardize end-to-end to INR: charge in INR and ensure order/invoice formatting uses INR consistently.

### Business objective
- Prevent accounting/payment inconsistencies and ensure correct customer-facing currency.

### Personas
- Customer (pays/receives invoice)
- Admin/accounting (reconciliation)

### Affected components
- dev/services/order_service.py (payment call)
- payments layer (adapter)
- invoice generation formatting

### Out of scope
- Real payment gateway integration (covered by separate enhancement ENH-012).

## Acceptance Criteria (BDD)

**Scenario: Charge uses INR**
- Given an order is submitted with valid items and totals
- When the system sends the charge request to the payment adapter
- Then the currency passed to the adapter is "INR"
- And the charged amount equals the order total in minor units if applicable (per existing adapter contract)

**Scenario: Invoice displays INR consistently**
- Given an order is successfully created and an invoice PDF is generated
- When the invoice is rendered
- Then the currency symbol and/or currency code shown is INR-consistent (₹ and/or "INR")
- And no part of the invoice shows "USD"

**Scenario: Regression - order creation unaffected**
- Given an order is submitted with valid items
- When payment succeeds
- Then the order status remains "PAID" (or existing success status)
- And invoice generation completes successfully

**Scenario: Negative - invalid currency configuration**
- Given the application is misconfigured with an unsupported currency code
- When an order is submitted
- Then the API responds with a validation/config error
- And no order is created
- And inventory is not decremented

## Related links
- Parent: VNK-10
- Issue links: none; subtasks: none; attachments: none; comments: 0
- Related enhancement referenced in text: ENH-012 (real payment gateway, out of scope)
