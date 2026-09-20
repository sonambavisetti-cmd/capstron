import os
from decimal import Decimal

import pytest

from dev.db import init_db, SessionLocal
from dev.models import Product
from dev.app.services.order_service import create_order
from dev.app.schemas import OrderCreate, CustomerIn, OrderItemIn


def setup_module(module):
    # Ensure DB tables exist for the test run (uses sqlite:///dev.db by default)
    init_db()


def test_create_order_basic():
    session = SessionLocal()
    # Create a product to be ordered
    p = Product(sku="TEST-001", name="Test Product", unit_price=Decimal("199.00"), quantity_available=10)
    session.add(p)
    session.commit()

    order_in = OrderCreate(
        customer=CustomerIn(full_name="Test User", email="test@example.com"),
        items=[OrderItemIn(product_id=p.id, quantity=1)],
        payment_method="COD",
    )

    res = create_order(session, order_in, idempotency_key=None)
    assert "order_id" in res
    assert res["total_amount"] == pytest.approx(199.0)

    session.close()
