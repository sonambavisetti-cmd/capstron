# Implementation Plan — VNK-92 / VNK-93 (ENH-009 Admin authorization)

## Objective
Secure the admin surface area by issuing a **Bearer token** on successful admin login and requiring that token for all **`/api/admin/*`** endpoints. Token expiry must be **7 days**. Use existing/default error envelope patterns already present in the codebase (no ENH-010 standardization in this scope).

## Scope
### In scope (approved)
- **Admin login** (`POST /api/admin/login`) returns an auth token.
- **Protect all admin endpoints** under `/api/admin/*` (e.g., order listing) so unauthenticated requests are denied.
- Token transport: **`Authorization: Bearer <token>`**.
- Token TTL: **7 days**.
- Add/update automated tests to cover the above.

### Out of scope
- UI/admin frontend pages (none currently described as part of the admin API feature).
- Global error envelope refactor (ENH-010).
- Role-based authorization beyond “is authenticated admin”.
- Token revocation/logout endpoint (not requested).

## Approved Enhancement → Jira Requirement Traceability
**Approved Enhancement**
- **VNK-VNK-2-ENH-009 — Admin authorization**

**Jira hierarchy**
- Epic: **VNK-91** — Secure Admin Authentication & Authorization (protect admin APIs)
  - Story: **VNK-92** — Admin login returns an auth token that can be used to call protected admin APIs
    - Subtask: **VNK-94** — Define token format, lifetime, and transport
    - Subtask: **VNK-95** — Implement admin token issuance in `/api/admin/login` response
  - Story: **VNK-93** — Admin endpoints require authentication and deny unauthenticated access
    - Subtask: **VNK-96** — Add auth middleware/decorator and apply to all `/api/admin/*` routes
    - Subtask: **VNK-97** — Add/Update automated tests for admin authentication enforcement

## Existing Architecture (relevant)
- Flask app with API blueprints under `dev/api/*`.
- Auth utilities referenced from `dev/auth.py` (password verification imported by admin login).
- Tests under `dev/tests/*` using pytest.

## Affected Components
- `dev/api/admin.py` — login endpoint and admin routes (e.g., orders listing).
- `dev/auth.py` — add token signing/verification helpers (or a new `dev/services/auth_tokens.py` if preferred; keep minimal).
- `dev/app.py` — only if app-level registration/helpers are needed (ideally avoid).
- `dev/tests/` — add/update tests for login token issuance and route protection.

## Frontend Changes
- None in this scope.
- Note: Any external client calling admin APIs must add `Authorization: Bearer <token>`.

## Backend Changes
### Token design (VNK-94)
- **Format:** Signed token string (recommended: `itsdangerous.URLSafeTimedSerializer` or similar built-in signing utility).
- **Claims/payload:**
  - `admin_id`
  - `iat` (issued-at) optional
- **Expiry:** Enforced to **7 days**.
- **Signing key:** Use Flask `app.config['SECRET_KEY']` (ensure exists) or existing secret location used by the app.

### Token issuance (VNK-95)
- Update `POST /api/admin/login` success response to include token:
  - Example (illustrative, keep current response fields as much as possible):
    ```json
    {"admin_id": 1, "token": "<signed>", "token_type": "bearer", "expires_in": 604800}
    ```
- On invalid credentials: preserve existing error style/status codes.

### Admin route protection (VNK-96)
- Create an `@admin_auth_required` decorator (or similar) that:
  - Reads `Authorization` header.
  - Validates `Bearer <token>` scheme.
  - Verifies signature and expiry.
  - Resolves and attaches admin context (e.g., `g.admin_id`) if needed.
  - On missing/invalid/expired token returns **401** (or current convention) with minimal error payload.
- Apply to **all** `/api/admin/*` routes except `/api/admin/login`.

## API Changes
### `POST /api/admin/login`
- **Request:** unchanged.
- **Response:** add token fields (`token`, `token_type`, `expires_in`).

### Protected admin routes
- **All `/api/admin/*`** (except login) must require:
  - `Authorization: Bearer <token>`
- **Unauthorized response:**
  - HTTP `401`
  - Body: keep default/error pattern used in codebase (e.g., `{ "error": "Unauthorized" }`).

## Database Changes
- None required.

## Test Impact (VNK-97)
Add/update pytest coverage:
1. **Login returns token**
   - Valid credentials → response includes `token`, `token_type=bearer`, `expires_in=604800`.
2. **Protected endpoint denies missing token**
   - Call `/api/admin/orders` without Authorization → 401.
3. **Protected endpoint denies invalid token**
   - `Authorization: Bearer abc` → 401.
4. **Protected endpoint allows valid token**
   - Obtain token via login; call `/api/admin/orders` with header → 200.
5. (Optional if feasible without time-mocking) **Expired token**
   - If token library supports timed tokens, add test using time travel/fake time; otherwise omit.

Files likely impacted:
- `dev/tests/test_admin_api.py` (create if not present) or extend existing admin/order tests.

## Implementation Tasks (implementation-ready)
### VNK-94 — Define token format/lifetime/transport
- [ ] Confirm `Authorization: Bearer` header usage in README/docstrings (minimal).
- [ ] Choose signing mechanism (prefer `itsdangerous` if already dependency; otherwise add minimal dependency if allowed).
- [ ] Define constants: `ADMIN_TOKEN_TTL_SECONDS = 7*24*60*60`.

### VNK-95 — Implement token issuance
- [ ] Add helper: `issue_admin_token(admin_id) -> str`.
- [ ] Update `/api/admin/login` response schema to include token, type, expiry.
- [ ] Ensure no sensitive fields are returned.

### VNK-96 — Add auth middleware/decorator
- [ ] Implement `require_admin_token(request) -> admin_id` (or decorator).
- [ ] Parse and validate `Authorization` header.
- [ ] Handle missing/invalid/expired with 401.
- [ ] Apply decorator to all admin routes besides login.

### VNK-97 — Tests
- [ ] Add tests for token issuance.
- [ ] Add tests for 401 without/invalid token.
- [ ] Add tests for successful access with valid token.

## Dependencies
- Python package availability:
  - Prefer **`itsdangerous`** (commonly bundled with Flask). Verify present in environment.
- Flask `SECRET_KEY` must be set; if not present, define minimal config behavior for dev.

## Risks & Mitigations
- **Risk:** SECRET_KEY not set consistently → tokens invalid across restarts.
  - Mitigation: Ensure app sets a stable secret in config for dev/prod; document requirement.
- **Risk:** Tests become brittle if token depends on time.
  - Mitigation: Use timed serializer and avoid asserting exact token value; only validate presence and behavior.
- **Risk:** Some admin routes may exist outside `dev/api/admin.py`.
  - Mitigation: Search for `/api/admin` registrations and ensure all are decorated.

## Implementation Sequence
1. Implement token helpers (VNK-94).
2. Update login endpoint to issue token (VNK-95).
3. Implement decorator and protect routes (VNK-96).
4. Add/adjust tests (VNK-97).
5. Run pytest locally.

## Definition of Done
- `/api/admin/login` returns a Bearer token with 7-day expiry metadata.
- All `/api/admin/*` routes (except login) return 401 when token missing/invalid.
- Valid token allows access to protected routes.
- Automated tests cover issuance + enforcement and pass.
- Planning artifacts committed and PR opened for human review.
