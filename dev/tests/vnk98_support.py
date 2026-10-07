"""Shared test support for VNK-98 (INR currency) tests.

Isolation: every fixture here builds its own SQLite engine under pytest's tmp_path
and rebinds SessionLocal in every module that captured it, so the tracked
dev.db file is never opened, regardless of what DATABASE_URL was at import time.
"""
from __future__ import annotations

import importlib.util
import re
import zlib
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def bind_temp_db(monkeypatch, tmp_path):
    """Create a temp DB and patch SessionLocal everywhere it is captured."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    import dev.db as dbmod
    import dev.models as models
    import dev.services.order_service as order_service
    import dev.services.invoice as flask_invoice
    import dev.api.invoices as invoices_api
    import dev.app.db as app_db
    import dev.app.services.pdf_worker as pdf_worker

    db_file = tmp_path / "vnk98_test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False}, future=True)
    models.Base.metadata.create_all(bind=engine)
    maker = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    for mod in (dbmod, order_service, flask_invoice, invoices_api, app_db, pdf_worker):
        monkeypatch.setattr(mod, "SessionLocal", maker, raising=True)

    storage = tmp_path / "storage"
    storage.mkdir()
    monkeypatch.setenv("STORAGE_PATH", str(storage))  # read at call time by the Flask renderer
    monkeypatch.setattr(pdf_worker, "STORAGE_PATH", str(storage))  # captured at import by the FastAPI renderer
    monkeypatch.delenv("ORDER_CURRENCY", raising=False)
    return maker, engine, storage


def seed_product(maker, sku="VNK98-1", price="199.00", qty=10):
    from dev.models import Product

    with maker() as s:
        p = Product(sku=sku, name="INR Test Product", description="", unit_price=Decimal(price),
                    quantity_available=qty, is_active=True)
        s.add(p)
        s.commit()
        return p.id


def order_payload(product_id, quantity=2, **extra):
    payload = {
        "customer": {"full_name": "INR Buyer", "email": "inr.buyer@example.com"},
        "items": [{"product_id": product_id, "quantity": quantity}],
        "payment": {"method": "COD"},
        "idempotency_key": "vnk98-key",
    }
    payload.update(extra)
    return payload


def count_rows(maker, *models):
    with maker() as s:
        return {m.__tablename__: s.query(m).count() for m in models}


class SpyProvider:
    """Mirrors dev.payments.mock.MockPayment: charge() returns an object with .success."""

    def __init__(self):
        self.calls = []

    def charge(self, amount_cents, currency, source, idempotency_key):
        from dev.payments.interface import PaymentResult

        self.calls.append({"amount_cents": amount_cents, "currency": currency,
                           "source": source, "idempotency_key": idempotency_key})
        return PaymentResult(success=True, provider_id="spy", message="spy")


def load_flask_app():
    """Load the Flask app from dev/app.py by path.

    `import dev.app` resolves to the FastAPI package dev/app/ (pre-existing name
    clash), so the module file is loaded explicitly.
    """
    spec = importlib.util.spec_from_file_location("vnk98_flask_app", REPO_ROOT / "dev" / "app.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.app.config.update(TESTING=True)
    return mod.app


def disable_pdf_compression(monkeypatch):
    """pypdf is not installed; ReportLab streams are compressed by default, so
    switch page compression off (test only) and search raw bytes."""
    import reportlab.rl_config as rl_config

    monkeypatch.setattr(rl_config, "pageCompression", 0)


def pdf_text(path) -> str:
    """Return the text-showing operands of an (uncompressed) PDF as one string.

    Also tries to inflate any Flate streams.
    """
    data = Path(path).read_bytes()
    chunks = [data]
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        try:
            chunks.append(zlib.decompress(m.group(1)))
        except Exception:
            pass
    text = b"\n".join(chunks).decode("latin-1")
    ops = re.findall(r"\(((?:\\.|[^\\)])*)\) Tj", text)
    return "\n".join(re.sub(r"\\(.)", r"\1", o) for o in ops)
