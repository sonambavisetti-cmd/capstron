# Test Execution Report

## Test Scope
- **Enhancement:** VNK-VNK-2-ENH-001
- **Epic/Story:** VNK-126 → **VNK-134** (Subtasks: VNK-135, VNK-136)
- **In scope:** Client-side validation + inline field errors for quote enquiry form on landing page (`/`).
- **Out of scope:** ENH-002..006, backend/API/DB changes.

## Code Review Gate
- Workflow context indicates: **APPROVED FOR TESTING** ✅

## Environment
- **OS:** Windows (local)
- **Repo root:** `C:/Users/SonamBavisetti/Desktop/Capstone/capstron`
- **Branch:** `feature/VNK-134`
- **Implementation commit:** `b7aaba7029bffdeee8d33ed176453b60cffa7cc0`
- **Testing artifacts commit:** `a373f66` (this report + tests)

## Test Cases (Gherkin)
Location: `tests/features/quote_enquiry_client_validation_vnk134.feature`

| Test ID | Jira Story | Scenario | Result |
|---------|------------|----------|--------|
| VNK-134-HP-001 | VNK-134 | Valid submission sends request and shows Sending state | NOT EXECUTED (env) |
| VNK-134-NEG-REQ-001 | VNK-134 | Required field validation prevents submit (name) | NOT EXECUTED (env) |
| VNK-134-NEG-REQ-002 | VNK-134 | Required field validation prevents submit (mobile_number) | NOT EXECUTED (env) |
| VNK-134-NEG-REQ-003 | VNK-134 | Required field validation prevents submit (product_category) | NOT EXECUTED (env) |
| VNK-134-NEG-EMAIL-001 | VNK-134 | Invalid email format prevents submit | NOT EXECUTED (env) |
| VNK-134-BOUND-PHONE-001 | VNK-134 | Phone too short prevents submit | NOT EXECUTED (env) |
| VNK-134-BOUND-PHONE-002 | VNK-134 | Phone too long prevents submit | NOT EXECUTED (env) |
| VNK-134-BOUND-PHONE-003 | VNK-134 | Phone has letters prevents submit | NOT EXECUTED (env) |
| VNK-134-REG-001 | VNK-134 | Inline error clears when corrected | NOT EXECUTED (env) |

**Total Gherkin scenarios:** 9

## Playwright Automation
- Location: `test-automation/tests/vnk134-quote-form-validation.spec.ts`
- **Total Playwright tests for VNK-134:** 8 (mapped below)

## Commands Executed
### Pytest
- `py -m pip install -r requirements.txt`
- `py -m pytest -q` (output captured to `storage/pytest-output.txt`)

### Playwright
- `cd test-automation`
- `npm test -- --workers=1` (output captured to `storage/playwright-output.txt`)

## Execution Summary
### Pytest Result
- **Status:** FAILED
- **Evidence:** `storage/pytest-output.txt`
- **High-level:** Multiple failures/errors in existing API tests (cart/products/orders). Errors indicate DB tables missing (e.g., `sqlite3.OperationalError: no such table: products`).

### Playwright Result
- **Status:** FAILED (web server did not start)
- **Evidence:** `storage/playwright-output.txt`
- **Root cause:** `ModuleNotFoundError: No module named 'flask'` when Playwright tried to start `python dev/app.py`.

## Failed Tests
### Pytest failures (regression)
- **Failure pattern:** `sqlite3.OperationalError: no such table: products` while seeding product data in test fixtures.
- **Classification:** **Environment/configuration issue** (DB init/migrations not applied in test DB or model metadata not registering tables at create time).
- **Evidence:** `storage/pytest-output.txt`

### Playwright failures
- **Failure:** webServer command exits with `ModuleNotFoundError: No module named 'flask'`.
- **Classification:** **Environment issue** (Playwright webServer uses a different Python runtime than `py`/system Python where Flask is installed).
- **Evidence:** `storage/playwright-output.txt`

## Defects / Issues
### Confirmed / Suspected Issues
1. **ENV-001:** Playwright webServer starts with `python` which resolves to an environment lacking Flask. Use `py` or a repo venv python executable in Playwright config.
   - Impact: Blocks all UI automation runs.
   - Classification: Environment/config issue.

2. **ENV-002:** Pytest DB setup creates tables but fixture cannot insert into `products` (table missing). Investigate model import/metadata registration or alembic migration expectations.
   - Impact: Existing regression suite failing.
   - Classification: Environment/config or test setup issue.

## Requirement Traceability
### Jira Story → Gherkin → Playwright → Result
| Jira Story | Gherkin Scenario | Playwright Test | Result |
|-----------|------------------|-----------------|--------|
| VNK-134 | Valid submission sends request and shows Sending state | VNK-134-HP-001 | BLOCKED (webServer) |
| VNK-134 | Required field validation prevents submit (name) | VNK-134-NEG-REQ-001 | BLOCKED (webServer) |
| VNK-134 | Required field validation prevents submit (mobile_number) | VNK-134-NEG-REQ-002 | BLOCKED (webServer) |
| VNK-134 | Required field validation prevents submit (product_category) | VNK-134-NEG-REQ-003 | BLOCKED (webServer) |
| VNK-134 | Invalid email format prevents submit | VNK-134-NEG-EMAIL-001 | BLOCKED (webServer) |
| VNK-134 | Phone too short prevents submit | VNK-134-BOUND-PHONE-001 | BLOCKED (webServer) |
| VNK-134 | Phone too long prevents submit | VNK-134-BOUND-PHONE-002 | BLOCKED (webServer) |
| VNK-134 | Phone has letters prevents submit | VNK-134-BOUND-PHONE-003 | BLOCKED (webServer) |
| VNK-134 | Inline error clears when corrected | VNK-134-REG-001 | BLOCKED (webServer) |

## Overall Test Status
- **OVERALL:** **BLOCKED / FAILED due to environment issues**
- **Human review required:** Yes — resolve ENV-001 and ENV-002, then re-run Playwright + Pytest.

## Artifact Locations
- Gherkin: `tests/features/quote_enquiry_client_validation_vnk134.feature`
- Playwright test: `test-automation/tests/vnk134-quote-form-validation.spec.ts`
- Pytest output: `storage/pytest-output.txt`
- Playwright output: `storage/playwright-output.txt`
- This report: `storage/test-execution-report-vnk134.md`
