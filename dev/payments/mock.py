from .interface import PaymentProvider, PaymentResult
import uuid

class MockPayment(PaymentProvider):
    def charge(self, amount_cents: int, currency: str, source: dict, idempotency_key: str) -> PaymentResult:
        # Always succeed in mocked adapter
        return PaymentResult(success=True, provider_id=str(uuid.uuid4()), message='mock-success')
