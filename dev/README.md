Vinayaka File Works - dev/ FastAPI backend (Phase 5 skeleton)

This folder contains a minimal FastAPI application and supporting skeleton
services created as part of Phase 5 (VNK-1). The implementation is intentionally
lightweight and contains TODOs for production integrations (Stripe, S3, Redis,
worker queue, etc.).

Quickstart (local development)

1. Create a Python virtual environment and install dependencies:

   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

2. Set required environment variables (see below). For local development a
   `.env` file may be used together with python-dotenv.

   - SECRET_KEY: a random secret string (required)
   - DATABASE_URL: SQLAlchemy database URL; default sqlite:///dev.db
   - REDIS_URL: optional redis url (redis://localhost:6379/0)
   - STORAGE_PATH: optional local storage path for generated PDFs (default ./storage)
   - STRIPE_API_KEY / STRIPE_WEBHOOK_SECRET: optional for payment integration

3. Initialize the database (creates tables using SQLAlchemy metadata):

   python -c "from dev.db import init_db; init_db()"

4. Run the FastAPI app (uvicorn):

   uvicorn dev.app.main:app --reload --host 0.0.0.0 --port 8000

API surface (Phase 5 minimal):

- GET /api/products
- GET /api/products/{id}
- POST /api/orders
- GET /api/orders/{id}
- GET /api/orders/{id}/invoice
- POST /api/payments/create-session
- POST /api/payments/webhook
- POST /api/admin/login (stub)

Notes & TODOs

- Idempotency-Key handling and Redis-backed reservations are left as
  TODOs in dev/app/services/* for TASK-07/TASK-09.
- Payment provider integration is stubbed in dev/app/services/payment_adapter.py
  — implement Stripe adapter and webhook signature verification for TASK-08.
- The PDF generator writes to a local `storage/invoices` folder by default.
  Replace with a storage adapter (S3/MinIO) in TASK-05.

Testing

- Basic pytest tests live under dev/tests/ and can be run with:

  pytest -q

  Note: tests in this skeleton use the local sqlite `dev.db` file and will
  create tables and temporary files during execution.
