from __future__ import annotations

import time
from typing import Any, Optional


class TTLCache:
    """Simple in-memory key/value cache with per-entry time-to-live expiry."""

    def __init__(self, ttl_seconds: int = 3600) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Returns cached value if present and not expired, else None."""
        if key in self._store:
            value, expires_at = self._store[key]
            if time.monotonic() < expires_at:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Stores value under key with the configured TTL."""
        self._store[key] = (value, time.monotonic() + self._ttl)

    def clear(self) -> None:
        """Removes all entries from the cache."""
        self._store.clear()


# Shared cache for loaded HF pipelines (24-hour TTL)
pipeline_cache = TTLCache(ttl_seconds=86400)
