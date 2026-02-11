"""Redis cache utilities."""
import json
import redis.asyncio as redis
from typing import Any, Optional
from .config import settings


class Cache:
    """Redis cache wrapper."""

    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.ttl = settings.redis_cache_ttl

    async def connect(self):
        """Connect to Redis."""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None

        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        if not self.redis:
            return False

        ttl = ttl or self.ttl
        return await self.redis.setex(
            key,
            ttl,
            json.dumps(value)
        )

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False

        return await self.redis.delete(key) > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.redis:
            return False

        return await self.redis.exists(key) > 0


# Global cache instance
cache = Cache()
