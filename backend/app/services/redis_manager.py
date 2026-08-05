import logging
import asyncio
from typing import Optional, Any
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("codesage.redis_manager")

_redis_pool: Optional[aioredis.Redis] = None
_in_memory_queue: asyncio.Queue = asyncio.Queue()


async def get_redis_client() -> Optional[aioredis.Redis]:
    """
    Returns an async Redis client instance.
    Returns None gracefully if Redis server is unavailable or connection fails.
    """
    global _redis_pool
    if not settings.REDIS_URL:
        return None

    if _redis_pool is None:
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0
            )
            # Ping test
            await client.ping()
            _redis_pool = client
            logger.info(f"Connected to Redis server at {settings.REDIS_URL}")
        except Exception as e:
            logger.warning(f"Redis connection failed ({e}). Falling back to in-memory async queue.")
            return None

    return _redis_pool


async def close_redis() -> None:
    """Closes global Redis connection pool cleanly."""
    global _redis_pool
    if _redis_pool is not None:
        try:
            await _redis_pool.close()
            logger.info("Closed Redis connection pool.")
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
        finally:
            _redis_pool = None


def get_in_memory_queue() -> asyncio.Queue:
    """Returns fallback in-memory asyncio queue for test/offline execution."""
    return _in_memory_queue
