"""Inventory reservation interface stub.

This module provides a small abstraction for reserving product quantities
using Redis (recommended) with an in-memory fallback for local development.

The real implementation should use Redis atomic operations (EVAL or
Lua scripts) to decrement reservation tokens and set a TTL. When the TTL
expires the tokens are released back to the available pool.

For Phase 5 we provide a lightweight in-memory fallback and clear TODOs for
production integration.
"""
from __future__ import annotations

import os
import time
from typing import Dict, Tuple, Optional

try:
    import redis
except Exception:  # pragma: no cover - optional dependency
    redis = None


class ReservationClient:
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis is not None:
            try:
                self._client = redis.from_url(self.redis_url)
            except Exception:
                self._client = None
        else:
            self._client = None

        # in-memory fallback: mapping token -> (product_id, qty, expire_ts)
        self._in_memory: Dict[str, Tuple[str, int, float]] = {}

    def reserve(self, product_id: str, quantity: int, ttl_seconds: int = 600) -> Optional[str]:
        """Attempt to reserve `quantity` for `product_id`.

        Returns a reservation token on success, or None on failure.

        TODO: implement Redis-based atomic reservation with proper key naming
        and expiry. This stub uses a simple in-memory store and does not
        interact with authoritative `quantity_available` in the DB.
        """
        if self._client is not None:
            # TODO: use Lua script to atomically decrement reservation tokens
            # and set a TTL key. Return a token if successful.
            return None

        # in-memory naive reservation
        token = f"res_{int(time.time()*1000)}_{product_id}"
        expire_ts = time.time() + ttl_seconds
        self._in_memory[token] = (product_id, quantity, expire_ts)
        return token

    def release(self, token: str) -> bool:
        """Release a reservation token. Returns True if released."""
        if self._client is not None:
            # TODO: remove Redis reservation key and increment available tokens
            return False

        return bool(self._in_memory.pop(token, None))

    def cleanup_expired(self) -> int:
        """Cleanup expired in-memory reservations. Returns number removed."""
        now = time.time()
        removed = 0
        for k, v in list(self._in_memory.items()):
            if v[2] < now:
                del self._in_memory[k]
                removed += 1
        return removed


# Example usage:
# rc = ReservationClient()
# token = rc.reserve(product_id='...', quantity=2)
# rc.release(token)
