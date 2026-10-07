"""Order currency policy (VNK-98).

The charge currency is a server-side setting, never client input.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = frozenset({"INR"})
DEFAULT_CURRENCY = "INR"
INVOICE_CURRENCY_LABEL = "INR"
ENV_VAR = "ORDER_CURRENCY"


class CurrencyConfigError(Exception):
    """Raised when the configured order currency is unsupported.

    Deliberately not a ValueError subclass so it is not mapped to a 400.
    The message is generic and never contains the configured value.
    """


def get_order_currency() -> str:
    """Return the validated order currency, read from the environment at call time."""
    raw = os.environ.get(ENV_VAR)
    if raw is None:
        return DEFAULT_CURRENCY
    value = raw.strip()
    if value not in SUPPORTED_CURRENCIES:
        logger.error("Unsupported %s configuration: %r", ENV_VAR, raw)
        raise CurrencyConfigError("unsupported currency configuration")
    return value
