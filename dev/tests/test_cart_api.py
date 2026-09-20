from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture(autouse=True)
def _use_tmp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")

    import importlib
    import dev.db as db

    importlib.reload(db)

    import dev.models  # noqa: F401

    db.Base.metadata.create_all(bind=db.engine)

    # seed a product
    from dev.models import Product

    with db.SessionLocal() as session:
        session.add(
            Product(
                sku="SKU-1",
                name="Test Product",
                description="",
                unit_price=Decimal("10.00"),
                quantity_available=100,
                is_active=True,
            )
        )
        session.add(
            Product(
                sku="SKU-2",
                name="Inactive Product",
                description="",
                unit_price=Decimal("5.00"),
                quantity_available=100,
                is_active=False,
            )
        )
        session.commit()

    yield


def _client():
    from dev.app import app

    app.config.update(TESTING=True)
    return app.test_client()


def _get_product_ids():
    import dev.db as db
    from dev.models import Product

    with db.SessionLocal() as session:
        rows = session.query(Product).order_by(Product.sku.asc()).all()
        return {p.sku: p.id for p in rows}


def test_get_empty_cart_returns_structure():
    client = _client()

    resp = client.get("/api/cart/cust-1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["customer_id"] == "cust-1"
    assert data["items"] == []


def test_add_to_cart_then_get():
    client = _client()
    ids = _get_product_ids()

    resp = client.post("/api/cart/cust-1/add", json={"item": {"product_id": ids["SKU-1"], "quantity": 2}})
    assert resp.status_code == 200

    cart = resp.get_json()["cart"]
    assert cart["totals"]["item_count"] == 2

    resp2 = client.get("/api/cart/cust-1")
    assert resp2.status_code == 200
    cart2 = resp2.get_json()
    assert cart2["totals"]["item_count"] == 2
    assert cart2["items"][0]["product_id"] == ids["SKU-1"]


def test_put_cart_item_sets_quantity():
    client = _client()
    ids = _get_product_ids()

    resp = client.put(f"/api/cart/cust-1/items/{ids['SKU-1']}", json={"quantity": 3})
    assert resp.status_code == 200
    cart = resp.get_json()["cart"]
    assert cart["totals"]["item_count"] == 3


def test_delete_cart_item():
    client = _client()
    ids = _get_product_ids()

    client.post("/api/cart/cust-1/add", json={"item": {"product_id": ids["SKU-1"], "quantity": 2}})

    resp = client.delete(f"/api/cart/cust-1/items/{ids['SKU-1']}")
    assert resp.status_code == 200
    cart = resp.get_json()["cart"]
    assert cart["items"] == []


def test_inactive_product_blocked():
    client = _client()
    ids = _get_product_ids()

    resp = client.post("/api/cart/cust-1/add", json={"item": {"product_id": ids["SKU-2"], "quantity": 1}})
    assert resp.status_code == 400
    assert "inactive" in resp.get_json()["error"]


def test_quantity_max_99():
    client = _client()
    ids = _get_product_ids()

    resp = client.post("/api/cart/cust-1/add", json={"item": {"product_id": ids["SKU-1"], "quantity": 100}})
    assert resp.status_code == 400
    assert "<= 99" in resp.get_json()["error"]
