# Design Review: VNK-98 - INR currency alignment for payments and invoices

Inputs: `requirements.md` (VNK-98), `architecture.md` (VNK-98). Supersedes the VNK-2 design review (backed up in `backups/pre-VNK-98_20261007-122226/`).
Method: document review only. No code was run and `architecture.md` was not modified. Severity: P0/P1 block approval, P2/P3 do not.

## Verdict: APPROVE

There are no unresolved P0 or P1 findings. All 9 functional and 4 non-functional requirements have an architectural answer, and the AC-4 ordering requirement is met by construction. Six P2/P3 findings remain. The P2 items should be settled in the implementation plan.

## Review summary

The design is small and proportionate: one new module (`dev/services/currency.py`), edits to the order service, the orders API and two invoice renderers, and no schema change or new dependency. The currency comes from server configuration only. The check runs before any database write, so AC-4 cannot leave partial state. Six ADRs cover the decisions that matter.

The user did not answer the 11 open questions. The architecture adopts nine assumptions and changes one (A-02: HTTP 500 instead of 400). Both choices satisfy the acceptance criteria. The architecture marks them as unconfirmed, and so does this review.

## Findings

| ID | Sev | Area | Finding | Recommendation |
|---|---|---|---|---|
| D-01 | P2 | Testability / dependencies | Section 9 plans to extract text from the generated PDFs to assert "INR" present and "USD" absent (AC-2). Section 8 says "no new libraries". ReportLab writes only PDFs, and its content streams are normally compressed, so a grep of the bytes proves nothing. A PDF text-extraction library is needed. `requirements.txt` has none. | The implementation plan names the extraction approach and adds it as a test-only dependency, or disables stream compression in the renderer for tests. Correct the "no new libraries" statement. |
| D-02 | P2 | Invoice integrity (AC-2) | The architecture says the built-in Helvetica font has no "₹" glyph. It defers the fix: verify at implementation time, and use an "INR " prefix only if the symbol does not render. A conditional design leaves the invoice format undecided, and the same invoice could differ between environments. | Decide in the plan: always print the explicit "INR" label and treat "₹" as optional. Any such check is one-time and must not become a runtime branch. |
| D-03 | P2 | Scope | `pdf_worker.py` is included as a renderer while the rest of the FastAPI path is excluded (A-08 vs A-10, Sections 2 and 13). This is a judgement call, and it has no ADR. If the owner wants zero FastAPI changes, AC-2 is met only for Flask-generated invoices. | Record it as a short ADR or an explicit plan decision, and have the user confirm it. |
| D-04 | P3 | API | HTTP 500 for the unsupported-currency case (ADR-02, A-02) is the architecture's own proposal. The ADR notes that a `ValueError` subclass would give 400 with no handler change. | The user decides. The tests assert whichever status is chosen. |
| D-05 | P3 | Configuration | `ORDER_CURRENCY` is the architecture's naming, and the matching is strict: exact `INR` after trimming, so lowercase `inr` is rejected. An empty string raises, while an unset variable defaults to INR. | Confirm the name and strictness, and cover the empty-string and unset cases in the unit tests. |
| D-06 | P3 | Testability | AC-1 can only be proved with a spy, because the mock ignores the currency. The design does not say how the spy is injected, and `payment_provider` may be a module-level object. AC-4 in Playwright needs a server started with a bad environment variable. | The plan states the patch point. Cover AC-4 in pytest, not Playwright, unless a second server is acceptable. |
| D-07 | P3 | Reliability (accepted) | The charge happens inside the open transaction, after the inventory decrement. The architecture records this as a latent issue for ENH-012, and also notes the `int(total*100)` truncation. | Accept. No action in this story. |

## Requirements coverage

| Requirement | Architecture answer | Status |
|---|---|---|
| FR-01 charge currency is INR | `get_order_currency()` result passed to `charge()` (Sections 3, 7; ADR-01) | Covered |
| FR-02 amount in minor units | Contract and ×100 unchanged (ADR-04) | Covered |
| FR-03 invoice shows INR | "Currency: INR" line and "(INR)" headings (ADR-05) | Covered, see D-02 |
| FR-04 no "USD" on the invoice | Fixed labels only, with a text assertion planned | Covered, see D-01 |
| FR-05 success path unchanged | Success statuses stay PROCESSING/SUCCESS | Covered |
| FR-06 error on unsupported currency | `CurrencyConfigError`, 500 response (ADR-02) | Covered, see D-04 |
| FR-07 no order created | Check before the session opens (ADR-03) | Covered |
| FR-08 no inventory change | Same ordering | Covered |
| FR-09 INR consistent in order and invoice | Charge and both renderers; no order surface is changed (A-07) | Covered by assumption |
| NFR-01 consistency | One currency source for charge and labels | Covered |
| NFR-02 backward compatibility | Default INR, no schema change, adapter unchanged | Covered |
| NFR-03 data integrity | No writes before validation | Covered |
| NFR-04 testability | Section 9 test plan | Covered, see D-01, D-06 |

## Security checklist

| Check | Result |
|---|---|
| Client cannot choose the charge currency | Pass: server configuration only, and a payload `currency` key is ignored |
| Input validation | Pass: strict allow-list of one value |
| Fail closed | Pass: an unsupported value stops order creation, with no fallback |
| Information disclosure | Pass: the response does not echo the configured value, and the detail goes to the server log |
| Secrets management | Pass: no secrets involved, and `ORDER_CURRENCY` is not sensitive |
| Authentication and authorization | Not affected: no endpoint or access rule changes |
| Injection | Pass: no new input reaches SQL or HTML, and invoice text uses fixed labels and database values |
| Data loss | Pass: no migration, no deletion, and old PDFs are untouched |

No security finding at any severity.

## Boundaries and ADR completeness

- **Folders:** Python changes are under `dev/` and the end-to-end tests are under `test-automation/`, as required.
- **ADRs:** ADR-01 to ADR-06 cover configuration, error status, check ordering, the adapter contract, invoice labelling and the data model. The only missing record is the scope choice in D-03.

## Conditions

None are required for approval. Before the implementation plan is final, the user should confirm D-03, D-04 and D-05. D-01 and D-02 should be settled in the plan.

## Gate

Awaiting the user's decision: approve | discuss | revise | stop. Phase 5 (implementation plan) does not start without an explicit approval.
