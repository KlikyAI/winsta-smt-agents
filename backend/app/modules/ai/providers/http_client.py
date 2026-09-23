"""AI HTTP Client Manager with persistent connection pooling.

Maintains shared httpx.AsyncClient instances across all AI providers to eliminate
repeated TLS handshakes and socket setup latency.
"""

import asyncio
from typing import Optional
import httpx
import structlog

logger = structlog.get_logger()

_client_lock = asyncio.Lock()
_shared_client: Optional[httpx.AsyncClient] = None


async def get_ai_http_client(timeout_seconds: float = 60.0) -> httpx.AsyncClient:
    """Return a shared pooled httpx.AsyncClient instance."""
    global _shared_client
    if _shared_client is not None and not _shared_client.is_closed:
        return _shared_client

    async with _client_lock:
        if _shared_client is None or _shared_client.is_closed:
            limits = httpx.Limits(
                max_keepalive_connections=50,
                max_connections=100,
                keepalive_expiry=30.0,
            )
            timeout = httpx.Timeout(
                connect=10.0,
                read=timeout_seconds,
                write=10.0,
                pool=10.0,
            )
            _shared_client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                follow_redirects=True,
            )
            logger.info("ai_http_connection_pool_initialized", max_connections=100, keepalive_expiry=30.0)
    return _shared_client


async def close_ai_http_clients() -> None:
    """Gracefully close the pooled client on application shutdown."""
    global _shared_client
    async with _client_lock:
        if _shared_client is not None and not _shared_client.is_closed:
            await _shared_client.aclose()
            _shared_client = None
            logger.info("ai_http_connection_pool_closed")
