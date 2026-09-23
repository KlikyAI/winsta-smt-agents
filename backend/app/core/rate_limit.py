"""Small Redis-backed fixed-window rate limiter for public/auth endpoints."""

import hashlib
from collections.abc import Callable, Awaitable

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


def rate_limit(scope: str, *, limit: int, window_seconds: int) -> Callable[..., Awaitable[None]]:
    """Return a FastAPI dependency enforcing a per-client request window.

    The limiter fails open when Redis is unavailable so an infrastructure
    outage does not take down authentication. Production Redis itself remains
    localhost-bound and should not be exposed publicly.
    """

    async def dependency(request: Request) -> None:
        # Nginx overwrites X-Real-IP before proxying. The backend port is
        # localhost-only, so an external client cannot bypass that boundary.
        client = request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")
        fingerprint = hashlib.sha256(client.encode("utf-8")).hexdigest()[:32]
        key = f"ratelimit:{scope}:{fingerprint}"
        try:
            redis = await get_redis()
            count = int(await redis.incr(key))
            if count == 1:
                await redis.expire(key, window_seconds)
            if count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please try again later.",
                    headers={"Retry-After": str(window_seconds)},
                )
        except HTTPException:
            raise
        except Exception:
            # Rate limiting is defense-in-depth; preserve availability if the
            # cache is temporarily unavailable.
            return

    return dependency
