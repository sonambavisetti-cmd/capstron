# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Vinayaka File Works storefront MVP (product catalog, cart/checkout, orders, invoices, quote enquiries, admin). Python backend under `dev/`, Playwright E2E tests under `test-automation/`, Gherkin specs under `tests/features/`. Work is tracked by Jira keys (e.g. `VNK-134`, `VNK-VNK-2-ENH-001`), which appear in branch names, commit prefixes (`[VNK-134]`, `[TEST][VNK-134]`) and code comments. Planning docs live at the repo root (`impl-plan.md`, `architecture.md`, `design-review.md`, `requirements.md`).

## Commands

Windows / PowerShell project; a venv lives in `.venv`.

```
pip install -r requirements.txt
$env:SECRET_KEY="dev-secret"
python -c "from dev.db import init_db; init_db()"      # create tables in dev.db (SQLite default)
python dev/scripts/seed_admin.py                        # optional admin seed
python dev/app.py                                       # Flask storefront on :5000
uvicorn dev.app.main:app --reload --port 8000           # FastAPI app on :8000

pytest -q                                               # pytest.ini sets pythonpath=.
pytest dev/tests/test_validation.py::test_name          # single test
alembic upgrade head                                    # migrations (alembic.ini -> sqlite:///dev.db)

cd test-automation; npx playwright test                 # all E2E
npx playwright test tests/vnk134-quote-form-validation.spec.ts   # single spec
```

Note: `requirements.txt` does not list FastAPI/uvicorn, though `dev/app/` needs them. No lint config exists. `DATABASE_URL` overrides the SQLite default.

## Architecture: two parallel backends in `dev/`

The repo contains two overlapping stacks that share a database file (`dev.db`) but **not** code. Check which one a file belongs to before editing.

1. **Flask storefront (legacy/MVP)** — `dev/app.py` (single file with the landing page HTML/CSS/JS inlined via `render_template_string`, including the quote form and its client-side validation) plus blueprints in `dev/api/*.py` (`products`, `cart`, `orders`, `admin`, `invoices`, `quote_requests`), registered one-by-one with failures swallowed and logged. Uses `dev/db.py` (`SessionLocal`, `Base`, `init_db`), `dev/models.py`, `dev/validation.py` (order and quote-enquiry payload validation with field aliases), `dev/services/`, `dev/auth.py` (werkzeug password hashing).
2. **FastAPI app (VNK-3)** — the `dev/app/` package (`main.py`, `api/`, `models.py`, `schemas.py`, `db.py`, `services/`, `auth_tokens.py`). Admin routes in `dev/app/api/admin.py` are protected by bearer tokens signed with `SECRET_KEY` (itsdangerous-style, see `auth_tokens.py`; falls back to an insecure dev key).

Gotcha: `dev/app.py` and the `dev/app/` package share the name `dev.app`. `import dev.app` resolves to the **package** (FastAPI), so `python dev/app.py` runs the Flask file as a script, but tests doing `from dev.app import app` get the FastAPI app. Keep this in mind when debugging import or test behaviour.

Other pieces: `dev/payments/` (interface + mock), `dev/storage/` (local/S3 adapters), `dev/workers/invoice_worker.py` (RQ/Redis PDF generation; also `dev/app/services/pdf_worker.py`), `dev/templates/invoice_template.html`, `alembic/` migrations, `storage/invoices/` (generated PDFs, untracked).

## Tests

- Backend pytest tests in `dev/tests/`; they use the real local `dev.db` and create files, so they are not isolated.
- `test-automation/playwright.config.ts` defaults `baseURL` to `http://127.0.0.1:8000` (override with `BASE_URL`), and its `webServer` runs `python dev/app.py` (Flask, port 5000) with `reuseExistingServer: true` — start the server on the port you intend to test, or set `BASE_URL`. Results go to `test-automation/test-results/results.json`.
- `test-automation/run-all-tests.{sh,bat}` are stale templates (reference a hotel-booking project); don't rely on them.
- Gherkin features in `tests/features/` mirror the Playwright specs (e.g. VNK-134 quote-form validation) and are documentation/traceability, not executed by a runner.

## Secrets

All secrets come from environment variables (`SECRET_KEY`, `ADMIN_PASSWORD`, `STRIPE_*`, `REDIS_URL`, `STORAGE_PATH`); `scripts/secret_scan.sh` scans for leaks. `dev.db` is tracked in git and shows as modified after running the app or tests.
