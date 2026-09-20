"""Payment adapter interface and a Stripe adapter stub.

The adapter pattern keeps the payment provider pluggable. For Phase 5 we
provide an interface and a test-mode Stripe adapter skeleton. Do NOT embed
secrets in code; read them from environment variables (STRIPE_API_KEY,
STRIPE_WEBHOOK_SECRET). Integration with Stripe is intentionally incomplete
and must be implemented as part of TASK-08.
"""
from __future__ import annotations

import os
from typing import Dict, Any


class PaymentAdapter:
    """Abstract adapter interface for payment providers."""

    def create_session(self, amount_cents: int, currency: str = "INR", metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        raise NotImplementedError


class StripeAdapter(PaymentAdapter):
    """A minimal Stripe adapter skeleton.

    TODO: Install `stripe` package and implement session creation and
    webhook signature verification. Use STRIPE_API_KEY and
    STRIPE_WEBHOOK_SECRET environment variables injected from your secret
    manager or CI environment.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("STRIPE_API_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        # Do not raise if not present here; allow the app to start in a limited
        # development mode. Fail fast in production by checking env presence in
        # startup health checks or tests.

    def create_session(self, amount_cents: int, currency: str = "INR", metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        # TODO: implement using stripe.checkout.Session.create(..., idempotency_key=...)
        # For Phase 5 provide a deterministic stubbed response.
        return {
            "session_id": "stub_session_123",
            "url": "https://example.com/checkout/session/stub_session_123",
            "status": "stubbed",
        }

    def verify_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        # TODO: verify signature using stripe.Webhook.construct_event
        # For now return a minimal structure expected by the webhook handler.
        return {"type": "payment_intent.succeeded", "data": {"object": {}}}
