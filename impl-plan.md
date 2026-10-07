# Implementation Plan: VNK-2 - Product Search and Filter

Sources: requirements.md, architecture.md, design-review.md (all VNK-2). Supersedes the VNK-134 plan (backed up in backups/pre-VNK-2_20261006-095100/).
Scope: `dev/` and `test-automation/` only. `dev/app/` (FastAPI) is not modified (ADR-1).

## 1. Summary

Add a Flask `GET /api/products/search` and `GET /api/products/filters`, new product attributes (category, material, specifications, size and customization child tables) via Alembic 0003, a `ProductSearchService`, a seed script, a search/filter UI block in `dev/app.py` under the existing marketing cards, pytest unit tests, and Playwright E2E tests covering AC1-AC7 plus a regression run of existing specs.

The design review verdict is REJECT (F-01..F-12). The user overrode it with "approved". Decisions incorporated here:

| Finding | Decision in this plan |
|---|---|
| F-01 (P1) | Text search covers `name`, `category`, `specifications`, `sku` AND `material`. Sizes are NOT text-searched. Tests must pass with seed data where "PVC" appears only in `material` (see TASK-03, TASK-09). This corrects A-3 in architecture.md; architecture.md is not edited here (out of scope), the plan is authoritative on this point. |
| F-02 (P1) | Accepted risk: feature runs on seeded sample data only; no real data source or admin path (R-01). No explicit user decision beyond the override. |
| F-03 (P2) | Material enum is enforced in the service layer (400 on invalid value). Migration 0003 adds NO DB CheckConstraint on `material`, because SQLite cannot add constraints through plain ALTER TABLE. Columns and indexes are added with `op.batch_alter_table`, to stay SQLite-safe. This deviates from the "CheckConstraint" detail in architecture section 4, as explicitly allowed by F-03. |
| F-04 (P2) | Chosen: the UI requests `limit=100` and shows "Showing N of TOTAL" whenever TOTAL > N. The count text is therefore never misleading. No pagination (out of scope). |
| F-05 (P2) | Regression gate: run the existing Playwright specs in `test-automation/tests/` (`vinayaka-storefront.spec.ts`, `vinayaka-checkout.spec.ts`) before and after the UI change. Note: `vnk134-quote-form-validation.spec.ts` named in architecture.md is not present in `test-automation/tests/` in the working tree (only the two files above); TASK-10 must check git history and run it if it exists, otherwise record it as absent. |
| F-06 (P2) | The `Cache-Control` header on `/search` and `/filters` is applied only when `FLASK_ENV`/config indicates production (`max-age=30` / `60`); outside production the header is `no-store`. E2E tests additionally use unique query strings where practical. |
| F-07 (P2) | Migration 0003 is tested against a COPY of `dev.db` (never the tracked file). Seed is an explicit step in test setup (not implicit on app start). |
| F-08 (P3) | The filter `<details>` is open by default at widths above 820px and collapsed by default at or below 820px; a mobile-viewport E2E test asserts filters are reachable (open the summary, then use controls). |
| F-09 (P3) | More than 10 terms in `q` returns 400 with a clear message. |
| F-10 (P3) | One E2E check for the customization filter, with seed data including customization values. |
| F-11, F-12 | Accepted; recorded in the risk register. |

Frontend contract (fixed here, per architecture 5.3): element IDs `product-search-input`, `filter-material`, `filter-size`, `filter-customization`, `clear-filters`, `results-count`, `product-grid`, `no-results`. Additional ID `filters-panel` for the `<details>`, and `search-error` for the fetch-failure message.

## 2. Task Breakdown

### TASK-01 - Baseline regression run of existing tests
- Description: Before any change, run existing pytest suite and existing Playwright specs; record pass/fail baseline so later failures are attributable. Check whether a `vnk134-*` spec exists (git history or elsewhere) and include it.
- Target files: none modified (read/run only): `dev/tests/*`, `test-automation/tests/*`.
- Depends on: none
- Satisfies: NFR-03; F-05
- DoD: Baseline results (pass/fail per file) captured in the task hand-off notes; any pre-existing failures are listed and not blamed on VNK-2; existence of the vnk134 spec confirmed or recorded as absent.

### TASK-02 - Model additions
- Description: Add `category`, `material`, `specifications` columns to `Product`; add `ProductSize` and `ProductCustomization` models with unique constraints and (value, product_id) indexes; add `ix_products_material`, `ix_products_category`, `ix_products_is_active`. No CheckConstraint on `material` (F-03). New columns nullable; relationships with cascade delete.
- Target files: `dev/models.py`
- Depends on: TASK-01
- Satisfies: FR-03, FR-04, FR-05, FR-11, NFR-02; F-03
- DoD: Models import cleanly; `create_all()` on a fresh in-memory SQLite creates all new tables and indexes; existing model tests/pytest still pass.

### TASK-03 - ProductSearchService
- Description: Implement `ProductSearchService` that builds the query: active products only; `q` trimmed, max 100 chars, split into terms (max 10, more raises a validation error that maps to 400, F-09); each term must match (case-insensitive substring, `%`/`_`/backslash escaped with `ESCAPE`) at least one of name, category, specifications, sku, OR material (F-01). Sizes are not text-searched. Filters: `material` validated in the service against {PVC, PP, BOARD} case-insensitively (F-03), `size` and `customization` via `EXISTS` subqueries, optional `category` exact case-insensitive. AND across everything. Order by name, id; `total` via COUNT over the same filter; `limit` default 50 max 100, `offset` >= 0. Also a `get_filter_options()` method (materials restricted to those present in active products, distinct sizes, customizations, categories). Normalize sizes/options uppercase-trimmed.
- Target files: `dev/services/product_search.py` (new)
- Depends on: TASK-02
- Satisfies: FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-10; F-01, F-03, F-09
- DoD: Service callable with a Session; a product with `material=PVC` and name "File A4" is returned for `q="PVC File"` (F-01 proof); `%` in `q` matches literally; invalid material raises a validation error; sizes are not matched by `q`; no string concatenation of user input into SQL; no `DISTINCT` row duplication for multi-size products.

### TASK-04 - Alembic migration 0003
- Description: Create `0003_product_search_attrs` (down_revision `0002_add_cart_tables`): add the three columns using `op.batch_alter_table`, create `product_sizes` and `product_customizations` with constraints and indexes, create the three product indexes. Reversible `downgrade` (drop indexes, tables, columns via batch). No CheckConstraint (F-03).
- Target files: `dev/alembic/versions/0003_product_search_attrs.py` or the repo's existing alembic versions directory (confirm the real path by locating `0002_add_cart_tables.py`; place 0003 beside it).
- Depends on: TASK-02
- Satisfies: FR-11, NFR-02; F-03, F-07
- DoD: On a COPY of `dev.db` (copied to a temp path, `DATABASE_URL` pointed at it; the tracked `dev.db` is never touched), `alembic upgrade head` succeeds, then `alembic downgrade 0002_add_cart_tables` succeeds, then upgrade again succeeds; existing product rows survive upgrade; `git status` shows `dev.db` unchanged by this task.

### TASK-05 - Search and filters API endpoints
- Description: In `products_bp` add `GET /api/products/search` (parse params, call service, return `{items, total, limit, offset, applied}`; items with `id, sku, title, description, category, material, sizes, customizations, price, inventory, image_url`; 400 `{"error": ...}` for invalid material, non-integer limit/offset, over-length params, over-10-terms; 200 with empty items for zero matches) and `GET /api/products/filters`. Cache headers per F-06: `public, max-age=30` (search) / `max-age=60` (filters) only in production, `no-store` otherwise. Existing `GET /api/products` and `/<id>` unchanged. Generic error messages, no stack traces.
- Target files: `dev/api/products.py`
- Depends on: TASK-03
- Satisfies: FR-10, FR-02, FR-06, NFR-02; F-06, F-09
- DoD: Endpoints respond per the architecture contract; `/api/products/search` is not captured by `/<product_id>`; existing product endpoint tests still pass; cache header differs by environment as specified.

### TASK-06 - Seed script
- Description: Idempotent seed script (upsert by `sku`) creating sample products across PVC, PP, BOARD with categories, specifications, multiple sizes (incl. A4 and at least one product without A4), and some customization options. Must include: a PVC product whose NAME and SPECIFICATIONS do not contain "PVC" yet has `material=PVC` and name containing "File" (F-01 fixture); at least one PVC "File" product available in A4; non-PVC products; at least one inactive product; more than 100 items is NOT required. Sizes/options stored uppercase-trimmed. Does not run on app start; invoked explicitly. Document usage in a header comment and in `dev/README.md` only if that file already documents scripts.
- Target files: `dev/scripts/seed_products.py` (new)
- Depends on: TASK-02 (TASK-04 for non-dev DBs)
- Satisfies: FR-01..FR-06 (data), NFR-03; F-02 (accepted risk), F-07, F-10
- DoD: Running twice yields identical row counts (idempotent); seed output lists counts; inactive product is present but not returned by search; data supports AC1-AC4 and the customization check.

### TASK-07 - Storefront UI block
- Description: In `dev/app.py` template, keep the three static marketing cards; add beneath them within `#products` a search/filter block: labelled search input, `<details id="filters-panel">` containing material/size/customization selects (each with "All" default) and a `clear-filters` button, `results-count` (aria-live polite), `product-grid`, `no-results` panel ("No products found", "Try a different search term or clear your filters.", plus a Clear All Filters button), `search-error` message ("Unable to load products. Please try again."). Inline IIFE: on load call `/api/products/filters` to populate options; call `/api/products/search` with `limit=100`; debounce 250 ms on typing, immediate on filter change and Enter; `AbortController` so the latest request wins; render only via `textContent`/DOM nodes (no `innerHTML` with API data, including echoed search text); count text "N products" or "Showing N of TOTAL" when TOTAL > N (F-04); Clear All resets all controls and re-queries. CSS: at max-width 820px controls stack single-column, 44px min touch height, one-column grid, `<details>` collapsed by default; above 820px `<details>` open by default and filters in a row (F-08). Set the open state on load and on viewport change via `matchMedia`. Existing quote form and its script stay untouched.
- Target files: `dev/app.py`
- Depends on: TASK-05, TASK-06 (data to render)
- Satisfies: FR-01, FR-02, FR-03, FR-04, FR-05, FR-06, FR-07, FR-08, FR-09, NFR-01, NFR-04; F-04, F-08
- DoD: All eight IDs plus `filters-panel` and `search-error` exist; manual check at desktop and 390px width; marketing cards and quote form still render; no `innerHTML` usage with API data (grep-verified); fetch failure shows the error message and not "No products found".

### TASK-08 - Unit tests (pytest)
- Description: Tests for the service and endpoints using an in-memory SQLite with `create_all()` and fixtures: AC1 style search (including the F-01 fixture where "PVC" is only in `material`), material filter, size filter (including a multi-size product and no duplicates), combined search+material+size (AC4), customization filter, zero results returns 200 with `total: 0`, `%`/`_` literal matching, case-insensitivity, multi-term AND, 11 terms returns 400 (F-09), invalid material 400, invalid limit 400, limit cap 100, inactive products excluded, deterministic ordering, `/filters` output, `/search` not shadowed by `<product_id>`, existing `GET /api/products` unchanged, cache header by environment (F-06). Add a migration test (or documented script) that runs upgrade/downgrade on a temp copy of `dev.db` (F-07), skipped with a clear message if the dev DB copy source is unavailable.
- Target files: `dev/tests/test_product_search.py` (new), optionally `dev/tests/test_migration_0003.py` (new)
- Depends on: TASK-03, TASK-04, TASK-05
- Satisfies: NFR-03, FR-01..FR-06, FR-10, FR-11; F-01, F-03, F-06, F-07, F-09
- DoD: New tests pass; full `dev/tests` suite passes (no regressions vs TASK-01 baseline); tests never touch the tracked `dev.db`.

### TASK-09 - Playwright E2E tests
- Description: Add `vnk2-product-search.spec.ts` covering AC1..AC7. Setup runs the seed script explicitly (against the DB the test server uses; confirm how `playwright.config.ts` starts the server and make the seed step part of setup, not implicit) (F-07). AC1: type "PVC File", assert matching items visible, non-matching hidden, count shown (and the F-01 fixture item appears). AC2: material=PVC shows only PVC. AC3: size A4 on a filtered view. AC4: search + material + size. AC5: Clear All resets inputs and shows all products. AC6: nonexistent term shows "No products found" and the clear action. AC7: at a 390px viewport, the filters summary is reachable, can be opened, and controls are usable, and the grid has no horizontal overflow (F-08). One check for the customization filter (F-10). One check for the error state by routing `/api/products/search` to a failure. Use unique query strings where practical and rely on `no-store` outside production (F-06). Use ID selectors from the frontend contract.
- Target files: `test-automation/tests/vnk2-product-search.spec.ts` (new); `test-automation/playwright.config.ts` only if needed to run the seed step (minimal change, e.g. globalSetup or webServer command).
- Depends on: TASK-06, TASK-07
- Satisfies: NFR-03, FR-01..FR-09, NFR-01; AC1-AC7; F-06, F-07, F-08, F-10
- DoD: New spec passes on desktop and mobile viewport runs; repeated runs are stable (run at least 3 times consecutively); no dependency on a prior test's state.

### TASK-10 - Regression gate and final verification
- Description: Re-run the full pytest suite and all Playwright specs (`vinayaka-storefront.spec.ts`, `vinayaka-checkout.spec.ts`, the new spec, and the vnk134 spec if present/recoverable per TASK-01). Compare with the TASK-01 baseline. Confirm `dev/app/` untouched, `git status` shows changes only under `dev/` and `test-automation/` for this feature (other pre-existing modifications such as the tracked `dev.db` noted but not altered by this work), and no new dependencies added.
- Target files: none modified (run only); fix-ups, if needed, go back to the owning task.
- Depends on: TASK-08, TASK-09
- Satisfies: NFR-03; F-05
- DoD: No regressions vs baseline; results listed per spec; `dev/app/` diff empty; requirement-to-test traceability table (below) confirmed.

## 3. Execution Order

1. TASK-01 (baseline)
2. TASK-02 (models)
3. TASK-03 (service) and TASK-04 (migration) - both depend only on TASK-02/03 as listed; TASK-04 can run in parallel with TASK-03
4. TASK-05 (API), TASK-06 (seed; can run in parallel with TASK-03/05 once TASK-02 is done)
5. TASK-07 (UI)
6. TASK-08 (unit tests; can begin alongside TASK-05 for service tests) and TASK-09 (E2E)
7. TASK-10 (regression gate)

Rationale: data layer first (everything depends on the model), service before API before UI, seed before UI/E2E so there is data to render, baseline first and regression gate last to meet F-05. Migration is validated early and separately on a DB copy (F-07).

## 4. Traceability

| Requirement | Tasks | Verified by |
|---|---|---|
| FR-01, FR-02 (AC1) | 03, 05, 07 | TASK-08, TASK-09 AC1 |
| FR-03 (AC2) | 03, 05, 07 | TASK-08, TASK-09 AC2 |
| FR-04 (AC3) | 02, 03, 07 | TASK-08, TASK-09 AC3 |
| FR-05 | 02, 03, 07 | TASK-08, TASK-09 customization check |
| FR-06 (AC4) | 03, 05 | TASK-08, TASK-09 AC4 |
| FR-07 (AC5) | 07 | TASK-09 AC5 |
| FR-08 (AC6) | 07 | TASK-09 AC6 |
| FR-09, NFR-01 (AC7) | 07 | TASK-09 AC7 |
| FR-10 | 05 | TASK-08 |
| FR-11, NFR-02 | 02, 04 | TASK-08 (migration), TASK-04 DoD |
| NFR-03 | 08, 09, 10 | - |
| NFR-04 | 07 | TASK-09 |
| NFR-05 | none (Not Specified) | recorded as R-05 |

## 5. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation / Owner task |
|---|---|---|---|---|
| R-01 | F-02 accepted: feature shows seeded sample data only; no real catalog source or admin path; user did not make an explicit decision beyond the override | High | High (business value) | Documented; seed script clearly labelled sample; follow-up story needed for catalog import/admin. TASK-06 |
| R-02 | Design review verdict remains REJECT; architecture.md still says material is not text-searched (A-3) and mentions a CheckConstraint | Certain | Medium (doc drift) | This plan is authoritative for F-01 and F-03; recommend updating architecture.md in a separate approved step |
| R-03 | SQLite migration limitation (F-03) | Medium | Medium | batch_alter_table, no DB constraint, service-layer enum. TASK-04 |
| R-04 | Migration or `init_db()` damages tracked `dev.db` (F-07, arch R-2) | Medium | High | Test on temp copy only; verify `git status` for dev.db. TASK-04, TASK-08 |
| R-05 | Existing storefront specs break from `#products` changes (F-05); vnk134 spec missing from working tree | Medium | Medium | Baseline + regression gate; keep marketing cards and quote form untouched. TASK-01, TASK-10 |
| R-06 | Stale cache causes flaky E2E (F-06); 30 s staleness in production | Medium | Medium | no-store outside production; unique queries. TASK-05, TASK-09 |
| R-07 | Count vs cap mismatch (F-04) | Low | Low | limit=100 and "Showing N of TOTAL". TASK-07 |
| R-08 | Mobile accessibility of collapsed filters (F-08) | Medium | Medium | Default open/closed per breakpoint plus a mobile E2E check. TASK-07, TASK-09 |
| R-09 | Unanswered open questions Q1-Q9 resolved only by assumptions A-1..A-9 (customization values, URL state, performance targets) | Medium | Medium | Assumptions kept cheap to change; performance target not a test gate |
| R-10 | LIKE scan performance at larger catalogs (ADR-3); text search cannot use indexes | Low (about 5,000 rows assumed) | Medium | Documented upgrade path to FTS/trigram; not in this story |
| R-11 | Two stacks define `/api/products` and Product (arch R-1, F-12); FastAPI stays out of sync | Certain | Low | Accepted; follow-up. `dev/app/` untouched |
| R-12 | No rate limiting; accessibility/browser support baseline only (F-11, NFR-05 Not Specified) | Medium | Low | Accepted; input bounds, wildcard escaping, textContent rendering implemented |
| R-13 | Alembic path ambiguity (the versions directory location not verified in this planning step) | Low | Low | Locate `0002_add_cart_tables.py` first and place 0003 beside it. TASK-04 |
