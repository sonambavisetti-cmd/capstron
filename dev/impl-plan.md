# Implementation Plan — VNK-2-ENH-001 (Admin Quote/Enquiry UX & workflow)

## Objective
Deliver an admin-triage workflow for Quote Enquiries by adding **admin-protected APIs** to list enquiries, view details, and update status + follow-up notes, with database support for notes and status constraints.

> Human-approved scope: **VNK-2-ENH-001 only**.

---

## Scope
### Approved Enhancement
- **VNK-2-ENH-001 — Quote/Enquiry UX & workflow (Admin tracking + status + notes)**

### Jira Requirements in Scope
- **Epic (existing)**: VNK-39 — Quote enquiries (end-to-end API wiring & persistence)
- **Stories**:
  - VNK-88 — Admin list enquiries
  - VNK-89 — Admin enquiry detail
  - VNK-90 — Admin update status/notes
- **Supporting Tasks (Jira hierarchy note: unparented due to config)**:
  - VNK-82 — Define admin enquiry workflow (statuses + allowed transitions)
  - VNK-83 — Implement admin API: list quote enquiries (pagination + sort)
  - VNK-84 — Implement admin API: get quote enquiry details by id
  - VNK-85 — Implement admin API: update quote enquiry status and follow-up notes
  - VNK-86 — Add QuoteEnquiry follow-up note field and status constraints (DB + migration)
  - VNK-87 — Protect admin enquiry endpoints with admin authentication/authorization

### Explicitly Out of Scope
- Any enhancements other than VNK-2-ENH-001
- A full admin UI (HTML pages) **unless confirmed** (see Clarifications)

---

## Requirement Traceability

| Enhancement | Jira Requirement | Acceptance Criteria (summary) | Component | Implementation Task | Test Impact |
|---|---|---|---|---|---|
| VNK-2-ENH-001 | VNK-88 (Story) | Admin can list enquiries with pagination, newest-first, and key triage fields; invalid paging → 400; unauth → 401/403 | `dev/api/admin.py` (new routes) + `dev/models.py` + `dev/db.py` | **T1** Add admin list endpoint `GET /api/admin/quote-enquiries` with `page`, `page_size`, `sort` | Update/add pytest API tests for pagination, ordering, auth |
| VNK-2-ENH-001 | VNK-89 (Story) | Admin can fetch full enquiry details; missing id → 404; unauth → 401/403 | `dev/api/admin.py` + `dev/models.py` | **T2** Add admin detail endpoint `GET /api/admin/quote-enquiries/<id>` | Add pytest tests for 200/404 and auth |
| VNK-2-ENH-001 | VNK-90 (Story) | Admin can update status to allowed value and persist notes; invalid status → 400; missing id → 404; unauth → 401/403 | `dev/api/admin.py` + `dev/models.py` + Alembic migration | **T3** Add update endpoint `PATCH /api/admin/quote-enquiries/<id>` (status + follow_up_notes) | Add pytest tests for valid/invalid updates, clearing notes behavior |
| VNK-2-ENH-001 | VNK-86 (Task) | Follow-up notes are persisted; status constraints enforced (chosen behavior documented) | `dev/models.py` + `alembic/versions/*` | **T4** Add DB fields/constraints + migration | Migration test coverage (apply migrations in CI if present) |
| VNK-2-ENH-001 | VNK-87 (Task) | Admin endpoints are protected | `dev/api/admin.py` + auth helper | **T5** Implement admin auth mechanism for these endpoints | Add pytest for 401/403 paths |
| VNK-2-ENH-001 | VNK-82 (Task) | Status set + transitions defined | `dev/validation.py` (or new helper module) + docs | **T0** Decide status vocabulary & transition policy | Tests for validation + transition enforcement |

Traceability chain example:

```text
VNK-2-ENH-001
  ↓
VNK-88
  ↓
T1 Implement admin list enquiries endpoint
  ↓
Blueprint: dev/api/admin.py + Model: dev/models.py
  ↓
Pytest API tests (pagination/order/auth)
```

---

## Existing Architecture (Repository Findings)

### Application type
- Single **Flask** application located under `dev/`
- SQLAlchemy models in `dev/models.py`
- DB setup in `dev/db.py` with `SessionLocal`, `engine`, and `Base`
- Alembic present (`alembic/`, `alembic.ini`) and imports `dev.models.Base.metadata`

### Existing Quote Enquiry endpoints
- Public endpoints exist in `dev/api/quote_requests.py`:
  - `POST /api/quote-enquiries` creates an enquiry
  - `GET /api/quote-enquiries` lists enquiries (currently **not admin-protected**, no pagination)

### Existing admin auth (partial)
- `dev/api/admin.py` includes `POST /api/admin/login` that verifies username/password against `AdminUser`
- No session/token issuance is present in current code; login returns `admin_id` only

### Tests
- Existing test module `dev/tests/test_quote_enquiries.py` covers:
  - create quote enquiry
  - list quote enquiries (public)

---

## Component Impact

### Frontend
- None required for API-only implementation.
- Optional (pending confirmation): add a minimal admin page for triage.

### Backend / API
- Add admin routes to `dev/api/admin.py` for enquiry list/detail/update.
- Reuse `QuoteEnquiry` model and `SessionLocal`.
- Add validation for paging params and status updates.

### Database
- Extend `quote_enquiries` table for follow-up notes and status constraints.

### Authentication/Authorization
- Implement a mechanism to authorize admin-only routes (see options in Backend Changes).

### Configuration
- Potentially add a config value for admin auth strategy (if token-based).

### Documentation
- Update README or `dev/README.md` with admin endpoints and example requests.

---

## Database Changes

Planned changes to `quote_enquiries`:
- Add `follow_up_notes` **TEXT NULL**
- Add/adjust `status` constraints:
  - Option A (recommended): `CHECK (status in (...))`
  - Option B: application-level validation only (if DB portability concerns)

Also consider:
- Add index for `created_at` if pagination needs it (SQLite won’t use it much, but Postgres will)

Alembic:
- Create new migration under `alembic/versions/` reflecting the above.

---

## API Changes

### New/Modified Admin Endpoints
All endpoints require admin auth.

1) **List enquiries**
- `GET /api/admin/quote-enquiries`
- Query params:
  - `page` (int, default 1, must be >= 1)
  - `page_size` (int, default 20, must be >= 1, max capped e.g. 100)
  - `sort` (optional; default `created_at_desc`)
- Response (proposed):

```json
{
  "items": [{"id": "...", "created_at": "...", "name": "...", "mobile_number": "...", "email": "...", "status": "..."}],
  "page": 1,
  "page_size": 20,
  "total": 123
}
```

2) **Get enquiry detail**
- `GET /api/admin/quote-enquiries/<id>`
- Response: full enquiry details including message/requirements and `follow_up_notes`.

3) **Update enquiry**
- `PATCH /api/admin/quote-enquiries/<id>`
- Body:

```json
{ "status": "IN_PROGRESS", "follow_up_notes": "Called customer..." }
```

- Validation:
  - invalid status → 400
  - missing id → 404
  - `follow_up_notes`: decide behavior for empty string (clear vs reject) — see Clarifications

### Existing Public Endpoints
- `GET /api/quote-enquiries` currently exists and is unauthenticated.
- No change required for this enhancement, but risk: admin list endpoint should not conflict with existing route.

---

## Frontend Changes

No frontend changes required (API-only scope).

If admin UI is required, it should be a follow-up story and would likely live under Flask templates (e.g., `dev/templates/`) with a simple table and detail view calling the admin APIs.

---

## Backend Changes

### Admin authorization approach (needs decision)
Current repo has `POST /api/admin/login` returning `{admin_id}` only. Options:

1) **Lightweight header-based admin id** (fastest, but weaker security):
- Client calls login and then sends `X-Admin-Id: <id>` header.
- Server verifies that admin id exists.

2) **Token-based** (recommended):
- On login, issue a signed token (e.g., itsdangerous / Flask session signed cookie) and require it on subsequent admin calls.

This plan assumes **token-based** if feasible with current dependencies; otherwise fall back to header-based for MVP.

### Validation
- Add a central validator for:
  - list paging params
  - status values
  - (optional) transition constraints

### Model updates
- Extend `QuoteEnquiry` with `follow_up_notes` column.
- Add constants/enums (Python-level) for allowed statuses.

---

## Test Impact

### Existing tests to update
- `dev/tests/test_quote_enquiries.py` may remain (public endpoints).

### New tests to add
- `dev/tests/test_admin_quote_enquiries.py` (recommended) to cover:
  - list requires auth (401/403)
  - list pagination and ordering
  - detail 200/404
  - update 200/400/404
  - status validation
  - notes update and notes clearing behavior

### Regression areas
- Ensure no breakage to existing `quote_requests` endpoints.
- Ensure `Base.metadata.create_all()` usage doesn’t conflict with migrations; avoid relying on it for production.

---

## Implementation Tasks

### T0 — Status workflow definition (VNK-82)
- **Description**: Finalize allowed status vocabulary and whether transitions are constrained.
- **Component/files**: `dev/validation.py` (or new `dev/app/` equivalent validator module), docs in this plan.
- **Dependency**: Human confirmation.
- **Outcome**: Documented status list and transition policy used by validation + DB check (if used).

### T1 — Admin list enquiries endpoint (VNK-83, supports VNK-88)
- **Description**: Implement `GET /api/admin/quote-enquiries` with pagination + sort.
- **Component/files**: `dev/api/admin.py`
- **Dependency**: T5 (auth helper) should be in place first.
- **Outcome**: Paginated response with total and items.

### T2 — Admin enquiry detail endpoint (VNK-84, supports VNK-89)
- **Description**: Implement `GET /api/admin/quote-enquiries/<id>`.
- **Component/files**: `dev/api/admin.py`
- **Dependency**: T5.
- **Outcome**: 200 with full details; 404 when not found.

### T3 — Admin update status/notes endpoint (VNK-85, supports VNK-90)
- **Description**: Implement `PATCH /api/admin/quote-enquiries/<id>`.
- **Component/files**: `dev/api/admin.py` + `dev/validation.py`
- **Dependency**: T0, T4, T5.
- **Outcome**: Status/notes updates validated and persisted.

### T4 — DB migration + model update (VNK-86)
- **Description**: Add `follow_up_notes` column and status constraint strategy.
- **Component/files**: `dev/models.py`, `alembic/versions/<new>.py`
- **Dependency**: T0.
- **Outcome**: Migration applies cleanly; model reflects schema.

### T5 — Protect admin enquiry endpoints (VNK-87)
- **Description**: Implement an admin auth decorator/helper and apply it to the new enquiry routes.
- **Component/files**: `dev/api/admin.py` (and possibly new `dev/api/auth_helpers.py`)
- **Dependency**: None.
- **Outcome**: Unauthenticated calls return 401/403 consistently.

### T6 — Documentation updates
- **Description**: Document endpoints, auth method, and example curl requests.
- **Component/files**: `README.md` or `dev/README.md` (TBD)
- **Dependency**: T1–T5.
- **Outcome**: Clear operator/dev documentation.

---

## Dependencies
- Human confirmation of:
  - status vocabulary + transition policy
  - follow_up_notes empty string behavior (clear vs reject)
  - whether admin UI is required or API-only is sufficient
- Alembic configured and usable in target deployment pipeline.

---

## Risks
- **Auth design gap**: current login endpoint doesn’t establish an authenticated session/token.
- **Confusion between public vs admin listing**: both exist; ensure naming and access are clear.
- **SQLite vs Postgres differences**: CHECK constraints and migrations behave differently across DBs.
- **Base.metadata.create_all()** in blueprints can mask missing migrations in dev; ensure production path uses Alembic.

---

## Implementation Sequence (Recommended)
1. T0 — Confirm status vocabulary & transitions
2. T5 — Implement admin auth mechanism/decorator
3. T4 — Add model + migration for follow_up_notes/status constraints
4. T1 — Add admin list API (pagination + ordering)
5. T2 — Add admin detail API
6. T3 — Add admin update API
7. Add/Update tests
8. T6 — Documentation updates

---

## Definition of Done
- `dev/api/admin.py` provides admin-protected endpoints for list/detail/update of quote enquiries per AC.
- `quote_enquiries` schema includes follow-up notes and chosen status constraint behavior.
- All new/updated pytest tests pass locally and in CI.
- Documentation updated with endpoint specs and auth usage.
- PR contains **plan only** (this document) until human approval for Design/Development.
