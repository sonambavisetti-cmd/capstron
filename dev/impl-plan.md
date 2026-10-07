# Implementation Plan — VNK-98 (INR currency alignment)

## Objective
Standardize currency handling end-to-end to **INR** for order payments and invoice presentation, eliminating the current mismatch where payments are charged in **USD** while invoices display **₹**.

## Scope (Validated)
**In scope (VNK-98 / ENH-002):**
- Payment charge requests use currency code **`INR`**.
- Invoice PDF and any order/invoice responses use INR-consistent presentation (₹ and/or `INR`) and do not show `USD`.
- Add a configuration/validation mechanism so misconfigured currency codes fail fast and do **not** create orders or decrement inventory.

**Out of scope (explicitly per Jira):**
- Real payment gateway integration (covered by **VNK-108 / ENH-012**).

## Requirement Traceability
| Approved Enhancement | Epic | Jira Requirement (Story) | Implementation Task | Component(s) | Test Impact |
|---|---|---|---|---|---|
| VNK-VNK-3-ENH-002 | VNK-10 | VNK-98 | Update payment charge currency to INR | `dev/services/order_service.py`, `dev/payments/*` | Unit/integration: assert adapter called with `INR` |
| VNK-VNK-3-ENH-002 | VNK-10 | VNK-98 | Ensure invoice displays INR consistently | `dev/services/invoice.py` | Unit/integration: invoice generation does not include `USD` |
| VNK-VNK-3-ENH-002 | VNK-10 | VNK-98 | Add config + validation for supported currency codes | `dev/config.py` (or existing config module), `dev/validation.py`, `dev/app.py` init | Tests: misconfig returns error; no DB side effects |

## Existing Architecture (Relevant)
- Flask app with Blueprints under `dev/api/*`.
- Service layer: `dev/services/*` (order creation triggers payment + invoice generation).
- Payments: currently `dev/payments/mock.py` is used by `dev/services/order_service.py`.
- Invoice generation: ReportLab PDF in `dev/services/invoice.py` saved under `storage/invoices/...`.
- Test stack: `pytest` (unit/integration); Playwright UI verification tests under `test-automation/`.

## Affected Components
- **Backend**
  - `dev/services/order_service.py`: currency passed to payment adapter.
  - `dev/payments/*`: confirm adapter contract for currency; adjust mock expectations if needed.
  - `dev/services/invoice.py`: ensure no hard-coded USD appears; ensure amounts/currency representation consistent.
  - `dev/validation.py` (or config validation location): validate supported currency code at request-time or startup.
  - `dev/app.py` (or config loader): wire currency config.

## Frontend Changes
- None required for this story (landing page quote flow is unrelated). If any UI displays currency code/symbol from API response, verify it still shows INR.

## Backend Changes (Planned)
1. **Currency configuration**
   - Introduce `DEFAULT_CURRENCY` (or similar) with default value `INR`.
   - Supported set initially: `{INR}` (or extendable list if the app expects more later).
   - Validation: if configured currency not supported, API should return an error and abort order creation.

2. **Payment call alignment**
   - Replace hard-coded `'USD'` argument in payment `charge(...)` call with configured currency (expected: `INR`).

3. **Invoice presentation alignment**
   - Audit invoice generation for any currency codes/symbols.
   - Ensure invoice uses INR consistently (₹ and/or `INR`).
   - Ensure no `USD` is rendered.

## API Changes
- No new endpoints.
- Error behavior change for misconfigured currency:
  - `POST /api/orders` should respond with a **4xx/5xx** (to be confirmed by existing error-handling conventions) and not create an order.

## Database Changes
- None expected for ENH-002.

## Test Impact
### Unit tests (pytest)
- Order service:
  - Assert payment adapter `charge` called with currency `INR`.
- Config/validation:
  - When currency is invalid/unsupported, assert:
    - API returns error.
    - No order is persisted.
    - Inventory is not decremented.

### Integration tests
- `POST /api/orders` happy path remains green; invoice generation still succeeds.

### UI/Playwright checks (if any exist for checkout)
- Verify no UI expectation relies on `USD`.

## Implementation Tasks (No app source code in this PR)
1. Review current payment adapter interface (`dev/payments/mock.py`) and order service usage.
2. Identify existing configuration pattern (env var, config object) and choose minimal consistent approach.
3. Update order service plan to use configured currency.
4. Update invoice formatting plan to ensure INR consistency.
5. Update/add unit/integration tests plan coverage.
6. Add developer notes for rollout (e.g., required env var if introduced).

## Dependencies
- None required to begin.
- Coordinate with **VNK-108 (payment adapter)** if adapter interface changes are needed; for this story, aim to keep adapter interface stable.

## Risks
- Hidden coupling: other code paths/tests may assert `USD` or rely on specific formatting.
- Error-handling consistency: must match existing API error schema; otherwise tests may be brittle.
- Amount units ambiguity (major/minor units) in adapter contract; must confirm current mock behavior before locking assertions.

## Implementation Sequence
1. Confirm current adapter contract and how amount is passed.
2. Add/configure default currency (`INR`).
3. Route currency through order service payment call.
4. Normalize invoice currency presentation.
5. Add/adjust tests.

## Definition of Done
- VNK-98 acceptance criteria satisfied:
  - Payment adapter receives currency `INR`.
  - Invoice rendering contains no `USD` and is INR-consistent.
  - Misconfigured currency produces an error and does not create an order or decrement inventory.
- `pytest` suite updated accordingly.
- Plan reviewed and approved by human reviewer.
