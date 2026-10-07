# Code Review: VNK-2 Product Search and Filter

Reviewer: SDLC step 06. Date: 2026-10-07. Scope: uncommitted working tree (dev/models.py, dev/api/products.py, dev/app.py, dev/services/product_search.py, dev/scripts/seed_products.py, alembic/versions/0003_product_search_attrs.py). Static review only; no tests written, no verification run. Design review verdict (REJECT, overridden by user) is carried via impl-plan.md, which is authoritative.

## 1. Summary

The implementation matches impl-plan.md closely and has no blockers. Queries use SQLAlchemy bound parameters, LIKE wildcards are escaped with an explicit ESCAPE clause, API data is rendered with textContent only (no innerHTML in dev/app.py), and input bounds are enforced. One small fix was applied (server-side logging of swallowed exceptions). Remaining items are minor or are known/accepted risks.

## 2. Findings

| ID | Severity | Finding | Status |
|---|---|---|---|
| R-1 | Low | The two generic `except Exception` handlers in `/search` and `/filters` returned 500 without logging, hiding root cause. | Fixed |
| R-2 | Low | `func.upper(Product.material) == X` and `func.lower(Product.category)` prevent use of `ix_products_material` / `ix_products_category`. Fine at about 5,000 rows (R-10 in plan); not an issue now. | Open, note |
| R-3 | Low | `Product.is_active.is_(True)` excludes rows where `is_active` is NULL (column is nullable, default True). Legacy rows inserted without a value would be invisible to search. | Open, note |
| R-4 | Low | `from __future__ import annotations` is placed before the module docstring in product_search.py and seed_products.py, so the docstring is no longer a real `__doc__`. Harmless. | Open, cosmetic |
| R-5 | Low | `limit` above 100 is silently capped to 100 (plan says "limit cap 100"; `applied`/`limit` in response reflects the cap). `limit<1` returns 400. Consistent with plan. | Accepted |
| R-6 | Low | Migration `downgrade` uses `batch_alter_table(...).drop_column`, which on SQLite recreates `products`. Other tables (order_items, cart tables) reference products; table recreate with FKs can misbehave depending on `PRAGMA foreign_keys`. Not exercised here. | Needs TASK-04 DoD check on a COPY of dev.db |
| R-7 | Info | UI `category` filter is supported by the API but has no UI control (not required by plan). | Accepted |
| R-8 | Info | `architecture.md` still says material is not text-searched (A-3) and mentions a CheckConstraint; plan overrides (plan R-02). | Doc drift, known |
| R-9 | Info | No rate limiting on the new public endpoints (plan R-12, accepted). | Accepted |

No Critical, High or Medium findings.

## 3. Fixes applied

Only one file edited: `C:\Users\SonamBavisetti\Desktop\Capstone\capstron\dev\api\products.py`.
- Added `import logging` and a module `logger`.
- Added `logger.exception(...)` inside the two generic `except Exception` handlers of `search_products` and `product_filters`. Client responses are unchanged (still generic messages, no stack traces); the detail now goes to server logs only. Import check (`import dev.api.products`) succeeded.

No other file was modified. Not touched: dev.db, alembic.ini, alembic/env.py, dev/app/, no commits or pushes.

## 4. Manual actions / left for the user

1. Run plan TASK-04 DoD on a COPY of dev.db: upgrade, downgrade to 0002, upgrade again (see R-6). Do not use the tracked dev.db.
2. Known issues, not fixed: alembic.ini lacks logger sections (KeyError on alembic commands); tracked dev.db is stamped 0001 but contains 0002 tables (upgrade on it would try to re-create them, so use a copy and stamp appropriately); dev/tests baseline failures unconfirmed.
3. Decide whether to treat NULL `is_active` as active (R-3) or backfill via seed/migration.
4. Update architecture.md for F-01/F-03 drift in a separate approved step.
5. Seeded sample data only (plan R-01): a follow-up story is needed for a real catalog source.
6. Tests (pytest, Playwright), baseline/regression runs (TASK-01, 08, 09, 10) remain for later phases.

## 5. Plan conformance

| Task | Result |
|---|---|
| TASK-02 models | Conforms: three nullable columns, ProductSize/ProductCustomization with unique constraints and (value, product_id) indexes, three product indexes, cascade relationships, no CheckConstraint. |
| TASK-03 service | Conforms: active only; q trimmed, max 100 chars, max 10 terms; per-term OR over name, category, specifications, sku, material (F-01); sizes not text-searched; material enum in service (F-03); size/customization via EXISTS (no duplicates); category exact case-insensitive; order by name, id; COUNT over the same filter; limit default 50/max 100; offset >= 0; `get_filter_options` with materials limited to those present. |
| TASK-04 migration | Conforms: down_revision 0002_add_cart_tables, batch_alter_table, index names match models, reversible, placed beside existing versions. Verification pending (R-6). |
| TASK-05 API | Conforms: response shape and fields as specified, 400 for invalid inputs, 200 with empty items, route registered before `/<product_id>` so not shadowed, F-06 cache headers by environment, existing endpoints unchanged. |
| TASK-06 seed | Conforms: upsert by SKU, F-01 fixture (PVC only in material, name contains "File"), A4 PVC file, non-A4 products, inactive product, uppercase normalization, explicit invocation only, counts printed. |
| TASK-07 UI | Conforms: all ten IDs present, details open/closed by matchMedia (F-08), debounce 250 ms, immediate on change/Enter, AbortController, limit=100 and "Showing N of TOTAL" (F-04), error panel distinct from no-results, Clear All in both places, 820px breakpoint, 44px targets. |

AC coverage (implementation side): AC1 search, AC2 material, AC3 size, AC4 combined, AC5 clear, AC6 no results, AC7 mobile layout are all supported by the code. Tests proving them are pending.

## 6. Security checklist

| Check | Result |
|---|---|
| SQL injection | Pass. All user input goes through SQLAlchemy expressions with bound parameters; no string-built SQL. |
| LIKE wildcard injection | Pass. `\`, `%`, `_` escaped and `escape="\\"` set on every LIKE. |
| XSS | Pass. Cards and options built with createElement/textContent; no innerHTML in dev/app.py; echoed search text not rendered; image_url not rendered; API returns JSON. |
| Input bounds | Pass. q 100 chars/10 terms; filter values 64 chars; limit/offset integer-parsed (max 10 digits), limit capped, offset non-negative; material allow-list. |
| Error handling | Pass. Generic messages, no stack traces to clients; details now logged server-side. |
| Authn/authz | N/A. Public read-only catalog endpoints; no mutations. |
| Rate limiting / DoS | Accepted risk (R-9); bounded query size and LIKE scan on small catalog. |
| Caching | Pass. `no-store` outside production, short public cache in production; error responses `no-store`. |
| Secrets / config | Pass. None added; seed never runs on app start; DATABASE_URL respected. |
| Dependencies | Pass. None added. |
| Scope | Pass. dev/app/ untouched (git status shows no changes there). |
