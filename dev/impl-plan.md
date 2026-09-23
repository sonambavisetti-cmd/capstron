# Implementation Plan — VNK-123 — Storefront UI: unify homepage/entrypoint (FastAPI)

## Objective
Deliver a **single, consistent storefront entry experience** by consolidating the current dual UI entrypoints:
- FastAPI UI router currently redirects `/` → `/products`
- Legacy Flask entrypoint (`dev/app.py`) also defines `/` with a separate marketing/quote landing page

The goal is to make **FastAPI the canonical UI entrypoint** and ensure `/` deterministically serves that experience.

## Scope (validated)
### Approval status
**APPROVE SELECTED**

### In scope
Only the explicitly approved enhancement is in scope:
- **VNK-VNK-1-ENH-001** — UI Entry / Navigation: consolidate dual UI entrypoints into a single, consistent storefront entry (prefer FastAPI)

### Out of scope
- Checkout validation/UX, cart UX, invoice download UX, transport-mode conditional fields, accessibility polish (these are separate enhancements from the gap analysis and are not approved in this scope).
- Creating new quote/contact UI flows (beyond navigation/link placeholders).

## Requirement traceability
Approved Enhancement → Jira Requirement → Implementation Task → Component → Test Impact

| Approved Enhancement | Jira Epic | Jira Requirement (Story) | Jira Task(s) | Implementation Task(s) (this plan) | Component(s) | Test Impact |
|---|---|---|---|---|---|---|
| VNK-VNK-1-ENH-001 | VNK-122 | VNK-123 | VNK-124 | Implement FastAPI home/landing page route + template; update `/` behavior to serve it | `dev/app/ui/routes.py`, `dev/templates/storefront/*` | Add/adjust tests for GET `/` and navigation to `/products` |
| VNK-VNK-1-ENH-001 | VNK-122 | VNK-123 | VNK-125 | Deprecate or clearly separate legacy Flask `/` landing page | `dev/app.py` | Add/adjust tests (if any) to ensure Flask root no longer conflicts; documentation checks |

## Existing architecture (relevant)
- **Primary app**: FastAPI monolith serving server-rendered storefront pages + JSON APIs.
  - UI router: `dev/app/ui/routes.py`
  - Templates: `dev/templates/storefront/*.html`
  - Static: mounted under `/static` in `dev/app/main.py`
- **Legacy/alternate entrypoint**: Flask app in `dev/app.py`.
  - Defines `/` with inline HTML including a “View all →” placeholder link.
  - Posts quote-enquiry data to `/api/quote-enquiries`.
- Current conflict: Two different “home” experiences depending on which server entrypoint is used.

## Canonical behavior decision (planning assumption)
Because explicit answers to earlier clarifications are not present in the approval message, this plan assumes the simplest, consistent UX:
- **FastAPI serves the canonical storefront homepage at `/`** (HTTP 200, no redirect).
- **FastAPI provides a real landing page template** (“Home”) with clear navigation to `/products`.
- **Flask root (`/`) is deprecated** and should no longer present the storefront/landing UX.

If product owner prefers `/` → `/home` redirect instead, implementation can be trivially adjusted (route + redirect), but this plan targets `/` = home page for deterministic entry.

## Affected components
### Backend (routing)
- `dev/app/ui/routes.py`
  - Replace or modify existing `GET /` behavior (currently redirects to `/products`).
  - Add any additional home routes if needed (e.g., `/home` as alias).
- `dev/app/main.py`
  - Ensure router registration order remains correct (verify UI router mounts before other catchalls, if any).
- `dev/app.py` (Flask)
  - Deprecate/relocate the legacy landing page.

### Frontend (templates/static)
- New or updated template(s) under `dev/templates/storefront/`:
  - `home.html` (new) OR reuse existing layout and create a minimal “home” page.
  - Update navigation links in shared layout if present (`layout.html`).

### Docs (optional but recommended)
- `README.md` and/or `QUICK_START.md` to clarify which entrypoint to use for the storefront.

## Frontend changes (FastAPI server-rendered)
### Home page template (new)
Create `dev/templates/storefront/home.html`:
- Extends existing `layout.html`.
- Minimal content:
  - Store name / short description
  - Primary CTA button/link: **“Browse products” → `/products`**
  - Optional secondary CTA: “Contact / Quote” (link target depends on existing UI; if none exists, link can be omitted or point to a placeholder route that returns a friendly message).

### Navigation consistency
- If `layout.html` contains a top nav, ensure there is a “Home” link to `/` and “Products” link to `/products`.

## Backend changes
### 1) FastAPI `GET /` should render the home page
In `dev/app/ui/routes.py`:
- Change existing root handler from redirect to `TemplateResponse("storefront/home.html", ...)`.
- Provide standard context used by other templates (e.g., `request`).

Optional compatibility:
- Provide `GET /home` as an alias redirecting to `/` or rendering the same template (only if beneficial; keep minimal).

### 2) Legacy Flask entrypoint behavior
In `dev/app.py`, ensure `/` no longer competes as a primary storefront landing experience.
Implementation options (pick one during implementation; this plan prefers Option A):
- **Option A (preferred):** Keep Flask app but change `/` to return a plain deprecation message with link to `/products` (served by FastAPI when using the FastAPI app), or a 410 Gone.
- Option B: Move the old landing page to `/legacy` (or `/quote`) and make `/` redirect to `/products`.

Because Flask and FastAPI are separate entrypoints, this is mostly to avoid developer confusion and to prevent “wrong server started” scenarios.

### 3) Remove placeholder link(s)
If any legacy HTML remains accessible (Flask `/legacy`), replace placeholder anchors (e.g., `href="#"`) with real storefront routes where appropriate.

## API changes
None.
- This enhancement is purely UI entry/navigation and template rendering.

## Database changes
None.

## Test impact
### Unit/integration tests (pytest)
Add/adjust tests under `dev/tests/`:
1. **FastAPI home route**
   - `GET /` returns 200.
   - Response contains expected CTA/link to `/products`.
2. **Existing products route still accessible**
   - `GET /products` returns 200.

If an existing test suite uses a specific `app` factory, follow that established pattern.

### UI automation (Playwright) — optional
If `test-automation/` includes Playwright or similar:
- Add a smoke test: open `/`, click “Browse products”, verify navigation to `/products`.

## Implementation tasks (breakdown)
### VNK-124 — Implement FastAPI home/landing page route + template
1. Inspect existing UI router (`dev/app/ui/routes.py`) and template structure.
2. Create `dev/templates/storefront/home.html` extending `layout.html`.
3. Update `GET /` route to render `home.html` (remove redirect to `/products`).
4. Update shared navigation in `layout.html` if needed.
5. Add/adjust pytest tests covering `/`.

### VNK-125 — Deprecate or clearly separate legacy Flask '/' landing page
1. Update `dev/app.py`:
   - Replace inline HTML landing page at `/` with a deprecation response (410 or simple message) OR move it to `/legacy`.
2. Ensure any remaining links (e.g., “View all”) point to real routes.
3. Update documentation to clarify FastAPI entrypoint is canonical for storefront.

## Dependencies
- Agreement on the canonical root behavior:
  - `/` renders home (assumed), OR `/` redirects to `/home`.
- Agreement on Flask handling:
  - Deprecate `/`, or relocate to `/legacy`.

## Risks & mitigations
- **Breaking deep links/bookmarks**: Previously `/` redirected to `/products`. Mitigation: home page contains a prominent “Browse products” CTA; optionally keep a short redirect route `/start` → `/products` if needed (not required).
- **Developer confusion about which server to run**: Mitigation: update README/QUICK_START with explicit command and expected root route.
- **Template/layout coupling**: Ensure `home.html` reuses existing layout and styles to avoid drift.

## Implementation sequence
1. Confirm existing UI router registration and template base (`layout.html`).
2. Implement `home.html`.
3. Change FastAPI `GET /` to render `home.html`.
4. Update or deprecate Flask `/` behavior.
5. Add/adjust tests.
6. Update docs (optional but recommended).

## Definition of Done
- FastAPI serves **`GET /`** as the canonical storefront homepage (HTTP 200) using a Jinja2 template.
- Homepage provides a functional navigation link/CTA to `/products`.
- Legacy Flask `/` no longer presents a conflicting storefront landing experience (deprecated/relocated).
- Automated tests updated/added for `/` behavior.
- Only planning artifact committed in this step: `dev/impl-plan.md`.
