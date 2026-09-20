Vinayaka File Works — Quick Start

1. Create a venv and install Python deps:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt

2. Initialize DB:
   set SECRET_KEY=dev-secret
   python -c "from dev.db import init_db; init_db()"

3. (Optional) Seed admin:
   python dev/scripts/seed_admin.py

4. Run app:
   set SECRET_KEY=dev-secret
   python -m dev.app

Playwright tests

cd test-automation
npx playwright test

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>