"""VNK-98 TASK-07(b)(c)(d): service-level tests with a spy on order_service.payment_provider."""
import pytest

import dev.services.order_service as order_service
from dev.models import Customer, Invoice, Order, OrderItem, Product
from dev.services.currency import CurrencyConfigError
from dev.tests.vnk98_support import SpyProvider, bind_temp_db, count_rows, order_payload, seed_product


@pytest.fixture()
def env(monkeypatch, tmp_path):
    maker, engine, storage = bind_temp_db(monkeypatch, tmp_path)
    spy = SpyProvider()
    monkeypatch.setattr(order_service, "payment_provider", spy)
    pid = seed_product(maker, price="199.00", qty=10)
    return maker, spy, pid


def test_spy_return_shape_matches_mock_payment():
    from dev.payments.mock import MockPayment

    real = MockPayment().charge(100, "INR", {}, "k")
    spy = SpyProvider().charge(100, "INR", {}, "k")
    assert hasattr(real, "success") and hasattr(spy, "success")
    assert real.success is True and spy.success is True


def test_ac1_charge_uses_inr_and_cents(env):
    maker, spy, pid = env
    order_service.create_order(order_payload(pid, quantity=2))
    assert len(spy.calls) == 1
    call = spy.calls[0]
    assert call["currency"] == "INR"
    assert call["amount_cents"] == int(199 * 2 * 100)


def test_payload_currency_is_ignored(env):
    maker, spy, pid = env
    order_service.create_order(order_payload(pid, currency="USD"))
    assert spy.calls[0]["currency"] == "INR"


def test_explicit_env_inr(env, monkeypatch):
    maker, spy, pid = env
    monkeypatch.setenv("ORDER_CURRENCY", " INR ")
    order_service.create_order(order_payload(pid))
    assert spy.calls[0]["currency"] == "INR"


def test_ac3_statuses_processing_success_and_invoice_ready(env):
    maker, spy, pid = env
    order = order_service.create_order(order_payload(pid, quantity=1))
    with maker() as s:
        o = s.get(Order, order.id)
        assert o.order_status == "PROCESSING"
        assert o.payment_status == "SUCCESS"
        assert "PAID" not in (o.order_status, o.payment_status)
        inv = s.query(Invoice).filter_by(order_id=order.id).one()
        assert inv.status == "READY"
        assert s.get(Product, pid).quantity_available == 9


def test_ac4_unsupported_currency_raises_before_any_db_write(env, monkeypatch):
    maker, spy, pid = env
    monkeypatch.setenv("ORDER_CURRENCY", "USD")
    with pytest.raises(CurrencyConfigError):
        order_service.create_order(order_payload(pid, quantity=3))
    assert count_rows(maker, Customer, Order, OrderItem, Invoice) == {
        "customers": 0, "orders": 0, "order_items": 0, "invoices": 0}
    with maker() as s:
        assert s.get(Product, pid).quantity_available == 10
    assert spy.calls == []


def test_currency_checked_before_payload_validation(env, monkeypatch):
    maker, spy, pid = env
    monkeypatch.setenv("ORDER_CURRENCY", "USD")
    with pytest.raises(CurrencyConfigError):
        order_service.create_order({})


def test_spy_is_sensitive_to_currency_value(env, monkeypatch):
    """Sensitivity check: if the service were to pass USD, the spy would record it."""
    maker, spy, pid = env
    monkeypatch.setattr(order_service, "get_order_currency", lambda: "USD")
    order_service.create_order(order_payload(pid))
    assert spy.calls[0]["currency"] == "USD"
