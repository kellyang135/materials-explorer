"""Redis cache utilities."""

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.core.config import settings


class RedisCache:
    """Async Redis cache client."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    async def get_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._client is None:
            self._client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await self.get_client()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set value in cache with optional TTL."""
        client = await self.get_client()
        ttl = ttl or settings.CACHE_TTL_SECONDS
        await client.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        client = await self.get_client()
        await client.delete(key)

    async def clear_pattern(self, pattern: str) -> None:
        """Clear all keys matching pattern."""
        client = await self.get_client()
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await client.delete(*keys)

    async def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None


# Global cache instance
cache = RedisCache()
