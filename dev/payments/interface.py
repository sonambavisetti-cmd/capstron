from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class PaymentResult:
    success: bool
    provider_id: str
    message: str = ''

class PaymentProvider(ABC):
    @abstractmethod
    def charge(self, amount_cents: int, currency: str, source: dict, idempotency_key: str) -> PaymentResult:
        raise NotImplementedError
