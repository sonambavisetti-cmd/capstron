from abc import ABC, abstractmethod
from typing import Protocol

class StorageAdapter(ABC):
    @abstractmethod
    def save(self, filename: str, data: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_signed_url(self, path: str, expires: int = 3600) -> str:
        raise NotImplementedError


def get_adapter(name: str='local') -> StorageAdapter:
    if name == 'local':
        from .local import LocalStorage
        return LocalStorage()
    raise NotImplementedError('Only local adapter implemented')
