"""VNK-98 TASK-08: Flask API tests for currency handling (FR-05..FR-08, AC-3, AC-4)."""
import pytest

import dev.services.order_service as order_service
from dev.api.orders import CURRENCY_CONFIG_ERROR_STATUS
from dev.models import Customer, Invoice, Order, OrderItem, Product
from dev.tests.vnk98_support import SpyProvider, bind_temp_db, count_rows, load_flask_app, order_payload, seed_product

EXPECTED_STATUS = 500  # D-04 (unconfirmed); single constant for this test module


@pytest.fixture()
def env(monkeypatch, tmp_path):
    maker, engine, storage = bind_temp_db(monkeypatch, tmp_path)
    spy = SpyProvider()
    monkeypatch.setattr(order_service, "payment_provider", spy)
    pid = seed_product(maker, price="50.00", qty=7)
    client = load_flask_app().test_client()
    return client, maker, spy, pid


def test_default_config_returns_201_and_processing(env):
    client, maker, spy, pid = env
    r = client.post("/api/orders", json=order_payload(pid, quantity=1))
    assert r.status_code == 201
    oid = r.get_json()["order_id"]
    g = client.get(f"/api/orders/{oid}")
    assert g.status_code == 200
    assert g.get_json()["status"] == "PROCESSING"
    assert g.get_json()["status"] != "PAID"
    assert spy.calls[0]["currency"] == "INR"


def test_usd_config_returns_500_exact_body_and_no_side_effects(env, monkeypatch):
    client, maker, spy, pid = env
    monkeypatch.setenv("ORDER_CURRENCY", "USD")
    r = client.post("/api/orders", json=order_payload(pid, quantity=2))
    assert r.status_code == EXPECTED_STATUS
    assert CURRENCY_CONFIG_ERROR_STATUS == EXPECTED_STATUS
    assert r.get_json() == {"error": "unsupported currency configuration"}
    assert "USD" not in r.get_data(as_text=True)
    assert count_rows(maker, Customer, Order, OrderItem, Invoice) == {
        "customers": 0, "orders": 0, "order_items": 0, "invoices": 0}
    with maker() as s:
        assert s.get(Product, pid).quantity_available == 7
    assert spy.calls == []


def test_payload_currency_ignored(env):
    client, maker, spy, pid = env
    r = client.post("/api/orders", json=order_payload(pid, currency="USD"))
    assert r.status_code == 201
    assert spy.calls[0]["currency"] == "INR"


def test_value_error_still_maps_to_400(env):
    client, maker, spy, pid = env
    r = client.post("/api/orders", json={"items": [], "customer": {"email": "a@b.c"}})
    assert r.status_code == 400
    assert r.get_json() == {"error": "order must contain items"}
