"""VNK-98 TASK-07(e): AC-2 for both invoice renderers: 'INR' present, 'USD' absent.

pypdf is not installed in this environment, so page compression is disabled in
the test (ReportLab rl_config.pageCompression = 0) and raw text operands are read.
"""
from decimal import Decimal

import pytest

import dev.services.order_service as order_service
from dev.models import Customer, Invoice, Order, OrderItem
from dev.tests.vnk98_support import (SpyProvider, bind_temp_db, disable_pdf_compression, order_payload,
                                     pdf_text, seed_product)


@pytest.fixture()
def env(monkeypatch, tmp_path):
    maker, engine, storage = bind_temp_db(monkeypatch, tmp_path)
    disable_pdf_compression(monkeypatch)
    monkeypatch.setattr(order_service, "payment_provider", SpyProvider())
    pid = seed_product(maker, price="125.50", qty=10)
    return maker, storage, pid


def _assert_inr(text):
    assert "Vinayaka File Works" in text  # proves the extractor can read this PDF
    assert "INR" in text
    assert "USD" not in text
    assert "Currency: INR" in text
    assert "(INR)" in text


def test_flask_renderer_via_create_order(env):
    maker, storage, pid = env
    order = order_service.create_order(order_payload(pid, quantity=2))
    with maker() as s:
        inv = s.query(Invoice).filter_by(order_id=order.id).one()
        assert inv.status == "READY"
        path = inv.pdf_path
    assert str(storage) in path  # written to the temp STORAGE_PATH, not repo storage/
    text = pdf_text(path)
    _assert_inr(text)
    assert "INR 251.00" in text  # total = 125.50 * 2


def test_fastapi_renderer(env):
    from dev.app.services.pdf_worker import generate_invoice_pdf

    maker, storage, pid = env
    with maker() as s:
        c = Customer(full_name="PDF User", email="pdf@example.com")
        s.add(c)
        s.flush()
        o = Order(customer_id=c.id, payment_method="COD", subtotal=Decimal("125.50"), total_amount=Decimal("125.50"))
        s.add(o)
        s.flush()
        s.add(OrderItem(order_id=o.id, product_id=pid, quantity=1, unit_price=Decimal("125.50"),
                        line_total=Decimal("125.50")))
        inv = Invoice(order_id=o.id, status="PENDING")
        s.add(inv)
        s.commit()
        inv_id = inv.id
    with maker() as s:
        path = generate_invoice_pdf(inv_id, db=s)
    assert str(storage) in path
    text = pdf_text(path)
    _assert_inr(text)
    assert "INR 125.50" in text
    with maker() as s:
        assert s.get(Invoice, inv_id).status == "READY"


def test_extractor_sanity_detects_usd(env, tmp_path):
    """Guard against a vacuous 'USD absent' check: the extractor must see text we write."""
    from reportlab.pdfgen import canvas

    p = tmp_path / "usd.pdf"
    c = canvas.Canvas(str(p))
    c.drawString(40, 700, "Currency: USD")
    c.save()
    assert "USD" in pdf_text(p)
