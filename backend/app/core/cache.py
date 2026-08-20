import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis.asyncio as redis

from app.core.config import get_settings

T = TypeVar("T")

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().REDIS_URL, decode_responses=True)
    return _redis_client


async def cached_json(key: str, ttl_seconds: int, loader: Callable[[], Awaitable[T]]) -> T:
    """Only for public, non-user-specific aggregate data (e.g. dashboard
    analytics) — never used for a response that varies per user, since the
    cache key carries no user identity and would leak data across users."""
    client = get_redis()
    try:
        cached = await client.get(key)
        if cached is not None:
            return json.loads(cached)
    except redis.RedisError:
        pass  # cache unavailable — fall through to computing fresh, never fail the request

    value = await loader()
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except redis.RedisError:
        pass
    return value
