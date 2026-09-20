Vinayaka File Works — Storefront MVP

This repository contains the Vinayaka File Works storefront MVP implemented as a single Python Flask application under dev/. It provides a simple product catalog, cart & checkout APIs, order persistence, and invoice generation scaffolding for a small business storefront.

Quick start

1. Create a virtual environment and install requirements:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # or use activate.bat on cmd
   pip install -r requirements.txt

2. Set SECRET_KEY and initialize the database:
   set SECRET_KEY=dev-secret
   python -c "from dev.db import init_db; init_db()"

3. Seed an admin (optional):
   python dev/scripts/seed_admin.py

4. Run the app:
   set SECRET_KEY=dev-secret
   python -m dev.app

Project layout

- dev/: Flask app, models, services, blueprints, templates
- test-automation/: Playwright verification tests for the storefront
- impl-plan.md: Implementation plan and task list
- design-review.md: Architecture/design review focusing on the storefront

Notes

- All secrets must be provided via environment variables. Do NOT commit secrets to the repo.
- This repo intentionally focuses on the Vinayaka storefront; unrelated hotel/booking artifacts have been removed.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>