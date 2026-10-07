# Design Review: VNK-2 - Product Search and Filter

Inputs: `requirements.md` (VNK-2), `architecture.md` (VNK-2). Supersedes the previous design review (backed up in `backups/pre-VNK-2_20261006-095100/`).
Scope: review only. The design is not changed here. Severity scale: P0 blocker, P1 must fix before approval, P2 should fix in the implementation plan, P3 note.

## Verdict: REJECT (revise required)

Two P1 findings are unresolved. The design is otherwise sound and needs small edits, not a redesign. Once F-01 and F-02 are resolved, the verdict becomes APPROVE.

## Requirements coverage

| Item | Covered by | Status |
|---|---|---|
| FR-01, FR-02 / AC1 | `q` param, `total`, results count | Gap: see F-01 |
| FR-03 / AC2 | `material` enum filter | Covered |
| FR-04 / AC3 | `size` via `product_sizes` EXISTS | Covered |
| FR-05 | customization dropdown (A-1) | Covered by assumption, no AC |
| FR-06 / AC4 | AND semantics across params | Covered |
| FR-07 / AC5 | Clear All Filters re-query | Covered |
| FR-08 / AC6 | "No products found" panel (A-6) | Covered |
| FR-09, NFR-01 / AC7 | 820px breakpoint, stacked controls | Covered, see F-08 |
| FR-10 | `GET /api/products/search` | Covered |
| FR-11, NFR-02 | indexes on filter columns | Covered, text search is a scan (ADR-3) |
| NFR-03 | pytest + Playwright plan | Covered |
| NFR-05 | baseline only | Not Specified in requirements, see F-11 |

## Findings

| ID | Sev | Area | Finding | Recommendation |
|---|---|---|---|---|
| F-01 | P1 | Coverage | Text search covers `name`, `category`, `specifications`, `sku` (architecture 4, 5.1). `material` and sizes are not searched. A-3 says material and size values are searched "via the same text field content in seed data", which depends on seed data happening to repeat them in the name or specs. AC1 searches "PVC File"; a product with `material=PVC` and name "File A4" would not match. The design contradicts itself on what "specifications" means. | Add `material` to the searched fields (a plain column, no join), and state in A-3 that sizes are not text-searched. Do not rely on seed text. |
| F-02 | P1 | Data / scope | U-1: the Products page is static and `Product` has no material, size, category or customization data. The feature works only on seeded sample data, with no real data source or admin path. The story does not say this is acceptable. Approving without a decision risks shipping a feature that shows sample data. | The user confirms that seeded sample data is acceptable for this story (record it as a decision), or the story scope is extended. |
| F-03 | P2 | Migration | 0003 adds a `CheckConstraint` on `material` to an existing table. SQLite cannot add constraints through plain `ALTER TABLE`, and `alembic.ini` targets SQLite. | Use `op.batch_alter_table` in 0003, or enforce the enum in the service layer and drop the DB constraint. Decide in the plan. |
| F-04 | P2 | UX consistency | The results count shows `total`, but the grid renders at most `limit` (default 50). With over 50 matches the count and the visible grid disagree, and pagination is out of scope. | Either the UI requests `limit=100` and states the cap, or shows "Showing N of TOTAL". Pick one in the plan. |
| F-05 | P2 | Regression | U-2: the three static marketing cards stay, and the new block is added beneath them. Existing storefront Playwright specs target `#products` and may be affected. | The plan must list and re-run the existing specs (`vinayaka-storefront`, `vnk134-*`) as a regression gate. |
| F-06 | P2 | Testing | `Cache-Control: public, max-age=30` on `/search` can serve stale results to the E2E tests after seed or reset, causing flaky AC checks. | Tests use unique query strings, or the plan disables caching outside production. |
| F-07 | P2 | Data | `init_db()` drops tables outside production and `dev.db` is tracked and already modified (R-2). The seed script upserts by `sku`, but a drop removes it all. | Seed runs as an explicit step in test setup. Test migration 0003 against a copy of `dev.db`, never the tracked file. |
| F-08 | P3 | Mobile / AC7 | Filters inside a collapsible `<details>` are hidden until opened on mobile, and "easily accessible" is not defined. The panel must be open by default on desktop. | The plan specifies default open state per breakpoint, and the E2E test asserts filters are reachable at a mobile viewport. |
| F-09 | P3 | API | The 10-term cap in section 7 has no stated behavior when exceeded (reject with 400 or truncate). | Specify 400 with a clear message. |
| F-10 | P3 | Coverage | FR-05 has no AC, so the customization filter will be lightly tested (A-1). | Accept, and add one E2E check if seed data has customization values. |
| F-11 | P3 | Security | No rate limiting (R-4), and accessibility and browser support are baseline only (R-5). All are Not Specified in the requirements. | Accept and record as known risks. The injection, LIKE-wildcard, XSS and input-bound controls in section 7 are adequate for a public read-only endpoint. |
| F-12 | P3 | Maintainability | The FastAPI `/api/products` and `Product` model stay out of sync with the new attributes (R-1). | Accept. Track as a separate follow-up. |

## Security, scalability, maintainability

- **Security:** adequate for a public read-only endpoint. Bound parameters, escaped `LIKE` wildcards, enum validation, bounded `limit` and `q`, `textContent` rendering, and no PII. No P0/P1 security finding.
- **Scalability:** reasonable for about 5,000 products (A-9). Text search is a scan; the upgrade path to FTS or trigram is documented in ADR-3. The 9 assumptions are labelled as unverified, and none is presented as a requirement.
- **Maintainability:** additive and reversible migration, a new service module, no new dependencies, and backward-compatible endpoints. The template grows larger, an accepted trade-off in ADR-6.

## Assumptions to confirm (A-1 to A-9)

The user did not answer the nine open questions. None of the assumptions is high-risk except A-3, which feeds F-01. A-1, A-2, A-5, A-6 and A-8 are cheap to change later.

## Gate

Decision needed from the user: approve | discuss | revise | stop.

- `revise` is recommended: apply F-01 to `architecture.md`, and record the F-02 decision.
- Phase 5 (Implementation plan) must not start until the verdict is APPROVE.

## Gate outcome

The user replied "approved" in their own message, after being told this overrides the REJECT verdict with F-01 and F-02 open. The review verdict itself is unchanged (REJECT). F-01 and F-02 are carried into the implementation plan as explicit items: F-01 as a required design correction (add `material` to searched fields), F-02 as accepted risk (seeded sample data only; no explicit user decision beyond the override).
