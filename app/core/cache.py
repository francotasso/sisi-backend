from __future__ import annotations

import json
from typing import Any

from upstash_redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

_redis: Redis | None = None
if settings.UPSTASH_REDIS_REST_URL and settings.UPSTASH_REDIS_REST_TOKEN:
    _redis = Redis(
        url=settings.UPSTASH_REDIS_REST_URL,
        token=settings.UPSTASH_REDIS_REST_TOKEN,
    )


async def cache_get(key: str) -> Any | None:
    if _redis is None:
        return None
    try:
        data = await _redis.get(key)
        if data is None:
            return None
        return json.loads(data) if isinstance(data, str) else data
    except Exception:
        return None


async def cache_set(key: str, ttl: int, value: Any) -> None:
    if _redis is None:
        return
    try:
        await _redis.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


async def cache_delete(pattern: str) -> None:
    if _redis is None:
        return
    try:
        cursor = 0
        while True:
            cursor, keys = await _redis.scan(cursor=cursor, match=pattern)
            if keys:
                await _redis.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass
