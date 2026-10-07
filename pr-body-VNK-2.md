# [VNK-2] Product search and filter

Base: main
Head: feature/VNK-2-product-search

## Summary
Adds search and filtering to the storefront Products section: search by name, category or specifications, and filter by material (PVC/PP/Board), size and customization, with a results count, a "Clear All Filters" control, a "No products found" state and a mobile layout. Backed by two new Flask endpoints and an additive Alembic migration.

**The feature runs on seeded sample data only.** The `Product` model had no material, size, category or customization data, and the Products section was three static marketing cards. This PR adds the columns and a seed script. A real catalogue source or an admin/import path is not part of the story and is not included.

## Changes
- `dev/api/products.py`: new `GET /api/products/search` and `GET /api/products/filters`. The existing `/api/products` and `/api/products/<id>` are unchanged. Cache headers apply only when `APP_ENV` or `FLASK_ENV` is `production`; otherwise `no-store`.
- `dev/services/product_search.py`: `ProductSearchService`. Case-insensitive substring search, terms AND-ed across name, category, specifications, sku and material. Material, size and customization filters use `EXISTS` subqueries, so multi-size products are not duplicated. `LIKE` wildcards are escaped, `q` is limited to 100 characters and 10 terms, and `limit` is capped at 100.
- `dev/models.py`, `alembic/versions/0003_product_search_attrs.py`: nullable `category`, `material`, `specifications` columns, `product_sizes` and `product_customizations` tables, and indexes. The migration uses `batch_alter_table` and has a reversible downgrade. The material enum is enforced in the service, not with a database constraint.
- `dev/app.py`: search and filter UI under the existing marketing cards in `#products`. 250 ms debounce, latest request wins, "Showing N of TOTAL", and a filter panel that is collapsed at or below 820px. API data is rendered with `textContent` only.
- `dev/scripts/seed_products.py`: idempotent seed (`python -m dev.scripts.seed_products`) with 9 sample products, one inactive. It never calls `init_db()`.
- Tests: `dev/tests/test_product_search.py`, `dev/tests/test_migration_0003.py`, `test-automation/tests/vnk2-product-search.spec.ts`.
- Docs: `user-story.md`, `requirements.md`, `architecture.md`, `design-review.md`, `impl-plan.md`, `review.md` (VNK-2 versions).

The FastAPI package `dev/app/` is not modified.

## Verification
Reported by the verification phase, not re-run for this description.
- New pytest: 40 of 40 pass (38 search tests, 2 migration tests). The migration test runs upgrade, downgrade to `0002_add_cart_tables` and upgrade again on a temp copy of the committed `dev.db`, and existing rows survive.
- New Playwright spec `vnk2-product-search.spec.ts`: 13 of 13 pass, covering AC1 to AC7 including a 390px mobile check and the search-failure error state.
- Full pytest after the change: 44 passed, 5 failed, 6 errors. The same 11 failures and errors occur without this change (`dev.app` resolves to the FastAPI package instead of `dev/app.py`; admin-auth 401s; a cart fixture error). They are not caused by this PR.
- Existing Playwright specs: 5 passed, 18 failed. None of the failures is attributed to this PR, but no baseline run against the old code exists for them.
  - `vnk134-quote-form-validation`: looks for a "Full Name" label, and `dev/app.py` labels the field "Name".
  - `vnk3-storefront-verification`: expects FastAPI endpoints and a seeded `VFW-1001`.
  - `vinayaka-storefront` and `vinayaka-checkout`: their `init_db()` calls reset a shared database, and parallel workers race on it.
- There is no true pre-change baseline: the implementation was already in the working tree when the baseline ran.
- The UI JavaScript was inspected by the review and exercised by the Playwright spec. Nothing else was run in a real browser.

## Reviewer notes
- The design review verdict was REJECT, with two P1 findings. The author overrode it and approved moving on:
  - F-01 (`material` was not text-searched, so a "PVC File" search could miss a PVC product): fixed in the plan and implementation, and covered by a fixture product whose name and specs never contain "PVC".
  - F-02 (feature works on seeded sample data only): accepted as a known risk, not resolved.
- Code review found no Critical, High or Medium issues. Open Low items: `upper()`/`lower()` wrappers prevent index use on material and category (fine at about 5,000 rows); `is_active IS TRUE` excludes rows where `is_active` is NULL; `from __future__` appears before the module docstring in two new files.
- The nine open requirement questions were never answered. The design uses labelled assumptions (customization is a single-select dropdown filled from catalogue data; category is searchable text only; search runs while typing; state is not kept in the URL; mobile reuses the 820px breakpoint). The performance target of about 5,000 products and p95 under 300 ms is an assumption, not a requirement, and was not measured.
- `architecture.md` still describes the material column as not text-searched and mentions a database constraint. The implementation plan overrides it on both points.
- Rate limiting, accessibility and browser support are not specified and not addressed beyond labelled controls and `aria-live` regions.

## Known environment issues, not changed here
- `alembic.ini` lacks the `[logger_sqlalchemy]` and `[logger_alembic]` sections, so `alembic` commands fail with `KeyError: 'logger_sqlalchemy'`. The migration was checked with a temp ini.
- The tracked `dev.db` is stamped `0001_initial` but already has the 0002 cart tables, and it lacks the new columns. Stamp it `0002_add_cart_tables` on a copy, then upgrade, before running the app or the seed against it.
- Running the existing pytest suite or Playwright specs without a temp `DATABASE_URL` resets `dev.db`. Set `DATABASE_URL` and `STORAGE_PATH` to temp locations first.

## How to try it
```
$env:SECRET_KEY="dev-secret"
$env:DATABASE_URL="sqlite:///C:/temp/vnk2.db"
python -m dev.scripts.seed_products
python dev/app.py
```
Open the Products section and try searching "PVC File", filtering by material and size, then "Clear All Filters".

Related issue: Jira VNK-2.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
