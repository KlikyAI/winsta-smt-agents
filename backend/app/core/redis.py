"""Redis connection management."""

from typing import Optional
import redis.asyncio as aioredis
from app.core.config import get_settings

settings = get_settings()


async def get_redis() -> aioredis.Redis:
    """Get or create a fresh Redis client instance for current loop."""
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close the Redis connection."""
    pass
