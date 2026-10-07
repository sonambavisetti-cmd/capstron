# Architecture: VNK-2 - Product Search and Filter

Source: requirements.md (VNK-2). Supersedes the VNK-134 architecture (backed up in backups/pre-VNK-2_20261006-095100/).

## 1. Overview

Customers and dealers need to find products by search term (name, category, specifications) and filter by material (PVC/PP/Board), size, and customization, without browsing the whole catalog.

Design in one paragraph: add a server-side search/filter endpoint, `GET /api/products/search`, to the Flask stack. Add searchable attributes to the `products` table through an Alembic migration (0003), with indexes. Make the Products section of the storefront page API-driven: a search box, filter controls, a results count, a "No products found" state, and a "Clear All Filters" control, all driven by small vanilla JS embedded in the existing Flask template. The same filter logic serves search, filters, and filter-option discovery.

### 1.1 Target stack decision

The feature targets the **Flask storefront stack**: `dev/app.py`, `dev/api/products.py`, `dev/db.py`, `dev/models.py`.

Reasons, grounded in the code:
- The Products page that the story says "exists" is rendered by `dev/app.py` (`#products` section, `render_template_string`). The FastAPI package `dev/app/` has no UI and does not serve any page.
- `dev/app.py` registers the Flask `products_bp`. Existing Playwright specs (`test-automation/tests/vinayaka-storefront.spec.ts`, `vnk134-quote-form-validation.spec.ts`) exercise this Flask page. The most recent VNK-134 work extended the same stack.
- The FastAPI `dev/app/` package is a parallel API (orders, invoices, admin, site settings) with its own `dev/app/models.py`, `dev/app/db.py`, and a `GET /api/products` that uses `skip`/`limit`. It is not wired to the storefront.

Consequence: `dev/app/` is **not modified**. Both stacks expose `/api/products`; this feature does not touch or reconcile that duplication (see risk R-1).

### 1.2 Current-state findings that shape the design

1. The Products section in `dev/app.py` is three hardcoded marketing cards ("Printed Forms", "Packaging Kits", "Files & Folders"), not a product list. There is no product grid backed by the database today.
2. `Product` in `dev/models.py` has only `sku, name, description, unit_price, quantity_available, image_url, is_active`. There is **no** category, material, size, or customization attribute. The requirements cannot be met by querying existing columns alone.
3. `GET /api/products` returns a bare JSON list (`id, sku, title, price, inventory`) with `page`/`per_page`. It must stay backward compatible.
4. Migrations are Alembic (`alembic/versions/0001_initial.py`, `0002_add_cart_tables.py`). `init_db()` drops and recreates tables outside production, so the model must be updated alongside the migration.
5. SQLite is the default (`sqlite:///dev.db`); `DATABASE_URL` may point to Postgres in production. Search SQL must be portable across both.

## 2. Component Diagram

```
 Browser (Products page, mobile + desktop)
 +-------------------------------------------------------------+
 | Search input | Material | Size | Customization | Clear All   |
 | Results count | Product grid | "No products found" panel    |
 |   [search-filter JS module inside dev/app.py template]      |
 +---------------------------+---------------------------------+
                             | GET /api/products/search?q=&material=&size=&customization=
                             | GET /api/products/filters
                             v
 +-------------------------------------------------------------+
 | Flask app (dev/app.py)                                      |
 |  products_bp (dev/api/products.py)                          |
 |    - parse + validate query params                          |
 |    - ProductSearchService (dev/services/product_search.py)  |
 |        builds SQLAlchemy query: q AND material AND size ... |
 +---------------------------+---------------------------------+
                             | SQLAlchemy Session (dev/db.py)
                             v
 +-------------------------------------------------------------+
 | DB (SQLite dev / DATABASE_URL prod)                         |
 |  products (+ material, category, size/customization)        |
 |  product_sizes, product_customizations (child tables)       |
 |  indexes (Alembic 0003)                                     |
 +-------------------------------------------------------------+
```

Data flow (search): the user types or changes a filter, the JS builds a query string, calls `/api/products/search`, receives `{items, total, applied}`, and renders the grid and the count. If `total == 0` it renders the "No products found" panel with a clear-filters action. "Clear All Filters" resets the controls and re-queries with no parameters. On page load, the JS calls `/api/products/filters` once to populate the dropdown options.

## 3. Components

| Component | Location | Responsibility | New / Changed |
|---|---|---|---|
| Products UI block | `dev/app.py` (template and inline script) | Search input, filter controls, results count, product grid, no-results panel, clear button, responsive layout | Changed (replaces static cards in `#products`) |
| Search endpoint | `dev/api/products.py` | `GET /api/products/search`: parse and validate params, call service, shape JSON | Changed |
| Filter options endpoint | `dev/api/products.py` | `GET /api/products/filters`: distinct available option values | Changed |
| ProductSearchService | `dev/services/product_search.py` | Build the query: text match AND-combined with filters, active products only, count, limit/offset | New |
| Product model additions | `dev/models.py` | New attribute columns and child models | Changed |
| Migration 0003 | `alembic/versions/0003_product_search_attrs.py` | Add columns, child tables, indexes; down_revision `0002_add_cart_tables` | New |
| Seed data | `dev/scripts/` (new seed script) | Sample products with materials and sizes so the page has data to show | New |
| Unit tests | `dev/tests/test_product_search.py` | Service and endpoint tests (pytest, matching existing `dev/tests/`) | New |
| E2E tests | `test-automation/tests/vnk2-product-search.spec.ts` (+ feature file if the repo convention requires) | Playwright/TypeScript coverage of AC1-AC7 | New |

Existing `GET /api/products` and `GET /api/products/<id>` are unchanged. Note: Flask routing must make `/api/products/search` and `/api/products/filters` resolve before the `<product_id>` converter. Flask prefers static rules over variable rules, so this is safe, but the IDs `search` and `filters` become reserved (UUIDs, so no collision).

## 4. Data Model

Existing table `products` gains columns (all nullable so existing rows stay valid):

| Column | Type | Purpose |
|---|---|---|
| `category` | String(100), indexed | Category name for search text (and an optional filter, see A-2) |
| `material` | String(16), indexed | One of `PVC`, `PP`, `BOARD` (enforced by CheckConstraint, nullable) |
| `specifications` | Text | Free-text specs (searched) |

New child tables (one-to-many, so a product can be available in several sizes or customizations, per AC3 "products available in A4"):

| Table | Columns | Constraints and indexes |
|---|---|---|
| `product_sizes` | `id` (uuid str PK), `product_id` (FK products.id), `size` (String(32)) | Unique(`product_id`,`size`); index on (`size`, `product_id`) |
| `product_customizations` | `id` (uuid str PK), `product_id` (FK), `option` (String(64)) | Unique(`product_id`,`option`); index on (`option`, `product_id`) |

Indexes (FR-11), in addition to the above: `ix_products_material`, `ix_products_category`, `ix_products_is_active`. Text search uses case-insensitive `LIKE` with `lower()` on `name`, `category`, `specifications`, and `sku`. A leading-wildcard `LIKE` cannot use a B-tree index, so the performance benefit comes from the attribute filter indexes. The documented upgrade path is Postgres `pg_trgm` or SQLite FTS5 if the catalog outgrows `LIKE` (ADR-3).

Normalization: sizes, materials, and options are stored uppercase-trimmed (e.g., `A4`, `PVC`); the API compares case-insensitively.

## 5. API Surface

### 5.1 `GET /api/products/search`

Query parameters (all optional):

| Param | Type | Rule |
|---|---|---|
| `q` | string | Trimmed, max 100 chars; split on whitespace into terms; every term must match at least one of name, category, specifications, sku (substring, case-insensitive). Empty or missing means no text filter |
| `material` | string | One of `PVC`, `PP`, `BOARD` (case-insensitive); otherwise 400 |
| `size` | string | Max 32 chars; matches a `product_sizes.size` row |
| `customization` | string | Max 64 chars; matches a `product_customizations.option` row |
| `category` | string | Optional exact (case-insensitive) match; see A-2 |
| `limit` | int | Default 50, max 100; non-integer returns 400 |
| `offset` | int | Default 0, minimum 0 |

Semantics: AND across all provided parameters (FR-06). Only `is_active = true` products. Order by `name`, then `id`, for deterministic results.

Response 200:
```json
{
  "items": [
    {"id": "...", "sku": "...", "title": "PVC File A4", "description": "...",
     "category": "Files", "material": "PVC", "sizes": ["A4","FC"],
     "customizations": ["Logo print"], "price": 45.0, "inventory": 120, "image_url": null}
  ],
  "total": 1,
  "limit": 50,
  "offset": 0,
  "applied": {"q": "PVC File", "material": "PVC", "size": "A4"}
}
```
`items` uses the existing field naming (`title`, `price`, `inventory`) for consistency with `GET /api/products`. `total` is the total matches before limit/offset and feeds the results count (FR-02). A zero-match query returns 200 with `items: []` and `total: 0` (not 404). Errors: 400 `{"error": "<message>"}`, the existing error shape. Cache: `Cache-Control: public, max-age=30`, consistent with the existing list endpoint (see R-3 for staleness).

### 5.2 `GET /api/products/filters`

Returns options derived from catalog data (A-5):
```json
{"materials": ["PVC","PP","BOARD"], "sizes": ["A4","FC"], "customizations": ["Logo print"], "categories": ["Files"]}
```
`materials` is the fixed enum, filtered to those that exist in active products. The others are distinct values from active products.

### 5.3 Frontend contract

Element IDs the Playwright tests rely on (to be fixed in the implementation plan): `product-search-input`, `filter-material`, `filter-size`, `filter-customization`, `clear-filters`, `results-count`, `product-grid`, `no-results`. Each control has an associated `<label>`; the results count and no-results region use `aria-live="polite"`.

## 6. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python 3, Flask (existing), blueprint `products_bp` | Under `dev/` |
| ORM | SQLAlchemy 2.x (`future=True`, existing) | `dev/db.py`, `dev/models.py` |
| Migrations | Alembic (existing), new revision 0003 | |
| DB | SQLite (dev), `DATABASE_URL` (prod, e.g. Postgres) | Portable SQL only |
| Frontend | Vanilla JS and CSS inside the Flask template | No new framework or build step; matches the existing quote-form script |
| Unit tests | pytest (existing `dev/tests/`) | |
| E2E tests | Playwright with TypeScript under `test-automation/` | |

No new third-party dependencies.

## 7. Security Considerations

- **SQL injection:** all filters use SQLAlchemy bound parameters. User text is never concatenated into SQL.
- **LIKE wildcard abuse:** `%` and `_` in `q` are escaped (`ESCAPE '\'`) so they are matched literally and cannot force full-table pattern scans.
- **Input bounds:** `q` max 100 chars, a cap of 10 terms, bounded `limit` (max 100), validated `material` enum. This limits query cost.
- **XSS:** the JS renders product fields with `textContent` / DOM node creation, never `innerHTML` with API data. Search text echoed in the no-results message is also inserted with `textContent`. Server-side, `jsonify` is used (no HTML rendering of user input).
- **Auth:** the endpoints are public read-only, like the existing product list. No PII is returned. Inactive products are never returned.
- **Rate limiting:** Not Specified in requirements (NFR-05). Not implemented; flagged in R-4.
- **Info disclosure:** errors return generic messages, without stack traces or SQL.

## 8. Scalability and Reliability

- **Query cost:** attribute filters use indexed columns and `EXISTS` subqueries on the child tables (avoids row duplication from joins and avoids `DISTINCT`). `total` comes from a `COUNT(*)` over the same filtered query. Fine for a catalog of thousands of rows (A-9). Beyond that, move to trigram or FTS indexes (ADR-3).
- **Pagination guard:** `limit`/`offset` exist to bound payloads even though the UI requirement does not ask for pagination. The UI requests the default page size; "load more" is out of scope.
- **Client behavior:** debounced requests (250 ms) on typing, and stale-response protection using `AbortController` (the latest request wins), so out-of-order responses do not render wrong results.
- **Caching:** `max-age=30` lets browsers and proxies absorb repeated identical queries. The filter-options endpoint can use a longer age (e.g. 60 s).
- **Statelessness:** the service holds no state, so it scales horizontally with the Flask workers; the DB is the only shared resource.
- **Reliability:** on a fetch failure the UI shows a distinct "Unable to load products. Please try again." message, not "No products found". The DB session is context-managed (`with SessionLocal()`), as in the existing code. The migration is additive and nullable-only, so it can be rolled back safely (`downgrade` drops the new indexes, tables, and columns).
- **Dev DB caveat:** `init_db()` drops all tables outside production, so seed data must be re-run after it. The seed script is idempotent (upsert by `sku`).

## 9. Assumptions for Open Questions (user did not answer)

These are recorded assumptions. Each is cheap to change and should be confirmed at the design review.

| # | Open question | Assumption adopted | Impact if wrong |
|---|---|---|---|
| A-1 | Customization filter options and values (Q1) | A single-select dropdown populated from distinct `product_customizations.option` values in the catalog. No fixed list is invented. If no product has customization data, the dropdown shows only "All". No acceptance criterion covers this, so it is built but tested only lightly. | Different values or semantics need data changes only; the filter mechanism stays |
| A-2 | Category filter (Q5) | **Category is searchable text only**, not a separate filter control: the story's filter list names only material, size, customization. The API accepts an optional `category` param and `/filters` returns `categories`, but the UI does not render a category control. | Adding a UI control is a small frontend change |
| A-3 | Matching rules (Q2) | Case-insensitive substring match; whitespace-separated terms are AND-ed, each term matching any of name, category, specifications, or sku. No fuzzy matching, stemming, or typo tolerance. "Specifications" means the new `specifications` column plus the size and material values (material and size values are searched via the same text field content in seed data; the service does not join child tables for text search). So "PVC File" matches a product whose name or specs contain both "PVC" and "File". | Fuzzy search would require ADR-3 FTS/trigram work |
| A-4 | Search timing (Q3) | Search runs as the user types, debounced 250 ms; filters apply immediately on change. Pressing Enter in the search box triggers an immediate search. No submit button is required. | Switching to submit-only is trivial |
| A-5 | Filter options source and selection mode (Q4/Q5) | Options come from catalog data via `/api/products/filters` (materials constrained to PVC/PP/BOARD). Material, size, and customization are each **single-select** with an "All" default. | Multi-select would change the API param format (repeat or comma list) |
| A-6 | AC6 suggestion wording (Q6) | Message: **"No products found"**, followed by the text "Try a different search term or clear your filters." and a **"Clear All Filters"** button inside the panel. Exact wording is a proposal. | Copy change only; E2E tests assert on "No products found" and the presence of the clear action |
| A-7 | URL state (Q7) | Not persisted. Search and filter state is held in the page only; reload resets it. Rationale: not in the ACs and not in the story's scope. The API is already URL-parameter based, so adding `history.replaceState` later is low cost. | Add URL sync in the frontend |
| A-8 | Mobile breakpoint and layout (Q8) | Reuse the existing `max-width: 820px` breakpoint in the page. Below it, controls stack in one column (full-width inputs, 44 px minimum touch height), the grid becomes one column, and the filter group sits in a collapsible `<details>` panel under the search box. Above it, filters are in a row. | CSS-only change |
| A-9 | Performance targets and catalog size (Q9) | No numeric SLA specified. Working target for design and test: catalog up to about 5,000 products, search p95 under 300 ms on the default SQLite or Postgres setup. This is a design assumption, not a verified requirement, and is not asserted as a hard test gate. | If the catalog is much larger, adopt ADR-3 upgrade |

Additional implicit assumptions: (a) the story's own Jira label list is informational (requirements item 11); (b) the catalog data must be created, since the DB has no material/size values today (see Section 10, U-1).

## 10. Unresolved Ambiguities and Risks

- **U-1 (blocking-level, data):** The Products page is currently static and `Product` has no material, size, category, or customization data. There is no source for this data in the story. The design adds the columns and a **sample seed script**, which means the feature will show sample data only until the business supplies real catalog data and an import/admin path. Admin product-management is not in this story and is **not** designed here. The user should confirm that seeded sample data is acceptable for this story.
- **U-2 (UI change):** Replacing the three static "Popular products" cards with a database-driven grid changes the visible home page. Whether to keep the marketing cards and add a separate "All products" section is not specified. Assumed: keep the three cards, and add the search/filter block with the grid beneath them within `#products` (the "View all" link anchors to it). This also keeps existing storefront Playwright specs valid; the implementation plan must verify them.
- **U-3:** Open questions Q1-Q9 are resolved only by the assumptions in Section 9.
- **R-1:** Two stacks both define `/api/products` and a `Product` model (`dev/models.py` vs `dev/app/models.py`). This feature updates only the Flask stack, so the FastAPI `ProductOut` will not expose the new attributes. This is a pre-existing duplication outside this story's scope.
- **R-2:** `init_db()` drops tables in non-production, so any real data in `dev.db` is lost on init. The repo's `dev.db` is tracked and already modified in the working tree; migration 0003 should be tested against a copy.
- **R-3:** The 30 s cache means catalog changes may take up to 30 s to appear in search.
- **R-4:** No rate limiting or bot protection (NFR-05 Not Specified).
- **R-5:** Accessibility and browser support are Not Specified; the design applies basic labelled controls and aria-live regions as a baseline, without claiming compliance.

## 11. ADRs

### ADR-1: Target the Flask storefront stack, not the FastAPI package
- Status: Proposed
- Context: Two stacks exist. Only Flask serves the Products page and is covered by the Playwright suite.
- Decision: Implement in `dev/app.py`, `dev/api/products.py`, `dev/models.py`, and a new `dev/services/product_search.py`. Leave `dev/app/` untouched.
- Consequences: Simple, consistent with VNK-134. The stack duplication remains (R-1).

### ADR-2: New endpoint `/api/products/search` instead of changing `/api/products`
- Status: Proposed
- Context: `/api/products` returns a bare list and may have consumers (cart, tests). The search needs a total count and metadata.
- Decision: Add a new endpoint with an envelope `{items, total, limit, offset, applied}`. Keep the old endpoints unchanged.
- Alternatives: Add params to `/api/products` (breaks the bare-array contract if the envelope is added; or leaves the count unavailable).
- Consequences: Backward compatible; two list-style endpoints coexist.

### ADR-3: SQL `LIKE` search with relational attributes now; FTS later
- Status: Proposed
- Context: Requirement asks for indexes (FR-11) but gives no scale target. SQLite dev and a possible Postgres production must both work.
- Decision: Portable case-insensitive `LIKE` over name, category, specifications, and sku, with B-tree indexes on filter columns. No FTS engine.
- Alternatives: SQLite FTS5 / Postgres `tsvector` or `pg_trgm` (better at scale but not portable and adds migration complexity); external search service (over-engineered).
- Consequences: Text matching is a scan, acceptable at about 5,000 rows (A-9). Revisit if the catalog grows.

### ADR-4: Child tables for sizes and customizations, enum column for material
- Status: Proposed
- Context: AC3 says "products available in A4", implying a product can have several sizes. Material is single-valued and fixed to three options.
- Decision: `material` as a nullable constrained column on `products`; `product_sizes` and `product_customizations` as one-to-many tables, queried with `EXISTS`.
- Alternatives: Comma-separated string columns (cannot be indexed or matched exactly); JSON column (not portable for querying on SQLite).
- Consequences: More tables, but correct and indexable filters.

### ADR-5: Server-side filtering with a debounced client
- Status: Proposed
- Context: The story requires a backend search API (FR-10) and supports large catalogs.
- Decision: The client does not filter locally; it calls the API (debounced 250 ms, with request cancellation) and renders the response.
- Alternatives: Load the whole catalog and filter in JS (does not scale, contradicts FR-10).
- Consequences: Network dependency, so an explicit error state is needed; results are always consistent with the DB.

### ADR-6: Vanilla JS in the existing template, no frontend framework
- Status: Proposed
- Context: The storefront is a single Flask-rendered template with an inline script (quote form). There is no build pipeline.
- Decision: Add the search/filter module as another self-contained IIFE in the template, using DOM-safe rendering (`textContent`).
- Consequences: Consistent and dependency-free; the template grows larger. Extracting it to a static file is an option for the implementation plan, not an architectural requirement.

### ADR-7: Additive Alembic migration plus model update
- Status: Proposed
- Context: Migrations are Alembic-managed, but dev uses `create_all()` via `init_db()`.
- Decision: Add `0003_product_search_attrs` (down_revision `0002_add_cart_tables`) and update `dev/models.py` in the same change. All new columns nullable; reversible downgrade.
- Consequences: No data loss on upgrade; tests may use `create_all()` and production uses Alembic.
