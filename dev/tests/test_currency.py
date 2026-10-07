"""VNK-98 TASK-07(a): unit tests for the currency policy module (FR-01, FR-06, D-05)."""
import pytest

from dev.services.currency import CurrencyConfigError, get_order_currency


def test_unset_defaults_to_inr(monkeypatch):
    monkeypatch.delenv("ORDER_CURRENCY", raising=False)
    assert get_order_currency() == "INR"


def test_explicit_inr(monkeypatch):
    monkeypatch.setenv("ORDER_CURRENCY", "INR")
    assert get_order_currency() == "INR"


def test_padded_inr_is_trimmed(monkeypatch):
    monkeypatch.setenv("ORDER_CURRENCY", "  INR \t")
    assert get_order_currency() == "INR"


@pytest.mark.parametrize("value", ["USD", "inr", "Inr", "", "   ", "EUR", "INR,USD"])
def test_invalid_values_raise(monkeypatch, value):
    monkeypatch.setenv("ORDER_CURRENCY", value)
    with pytest.raises(CurrencyConfigError):
        get_order_currency()


def test_error_is_not_value_error_and_message_is_generic(monkeypatch):
    monkeypatch.setenv("ORDER_CURRENCY", "USD")
    with pytest.raises(CurrencyConfigError) as ei:
        get_order_currency()
    assert not isinstance(ei.value, ValueError)
    assert "USD" not in str(ei.value)


def test_read_at_call_time(monkeypatch):
    monkeypatch.setenv("ORDER_CURRENCY", "USD")
    with pytest.raises(CurrencyConfigError):
        get_order_currency()
    monkeypatch.setenv("ORDER_CURRENCY", "INR")
    assert get_order_currency() == "INR"
