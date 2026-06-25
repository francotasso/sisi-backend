from __future__ import annotations

import time
from typing import Any

_cache: dict[str, tuple[float | None, Any]] = {}


def _match_pattern(pattern: str, key: str) -> bool:
    if pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    return key == pattern


async def cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at is not None and time.monotonic() > expires_at:
        del _cache[key]
        return None
    return value


async def cache_set(key: str, ttl: int, value: Any) -> None:
    expires_at = time.monotonic() + ttl if ttl > 0 else None
    _cache[key] = (expires_at, value)


async def cache_delete(pattern: str) -> None:
    keys_to_delete = [key for key in _cache if _match_pattern(pattern, key)]
    for key in keys_to_delete:
        del _cache[key]


def clear_cache() -> None:
    _cache.clear()
