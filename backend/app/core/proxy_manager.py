"""Proxy Rotation and Anti-Rate-Limit Manager for Trend Collectors.

Provides resilient HTTP client dispatching with:
- Multi-proxy round-robin and health tracking.
- Cooldown on failing or rate-limited proxies.
- Realistic rotating User-Agent headers.
- Exponential backoff with jitter on HTTP 429 / connection timeouts.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable, Coroutine, Optional

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()

# Realistic modern Desktop & Mobile User-Agents across platforms
USER_AGENTS = [
    # Chrome Desktop (Mac / Windows / Linux)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    # Safari Desktop
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    # Edge Desktop
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    # Mobile iOS Safari & Android Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.88 Mobile Safari/537.36",
]


class ProxyPoolManager:
    """Manages rotating proxy pool, failure detection, and backoff retries."""

    def __init__(self) -> None:
        self._proxies: list[str] = []
        self._failing_proxies: dict[str, float] = {}  # proxy -> cooldown_until_timestamp
        self._index: int = 0
        self._cooldown_seconds: float = 300.0  # 5 min cooldown on 429 / persistent errors
        self.reload_proxies()

    def reload_proxies(self) -> None:
        """Parse proxy list from environment settings."""
        settings = get_settings()
        raw = settings.proxy_list or ""
        # Support comma or newline/semicolon separated list
        items = [
            p.strip()
            for p in raw.replace(";", ",").replace("\n", ",").split(",")
            if p.strip() and not p.strip().startswith("#")
        ]
        self._proxies = items
        self._failing_proxies.clear()
        self._index = 0
        if self._proxies:
            logger.info("proxy_pool_initialized", count=len(self._proxies))

    @property
    def has_proxies(self) -> bool:
        return bool(self._proxies)

    def get_random_user_agent(self) -> str:
        """Return a random real-world browser User-Agent."""
        return random.choice(USER_AGENTS)

    def get_default_headers(self, extra: Optional[dict[str, str]] = None) -> dict[str, str]:
        """Build standard anti-bot request headers."""
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8,ar;q=0.7",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
        }
        if extra:
            headers.update(extra)
        return headers

    def get_next_proxy(self) -> Optional[str]:
        """Retrieve the next healthy proxy via round-robin."""
        if not self._proxies:
            return None

        now = time.time()
        # Clean expired cooldowns
        expired = [p for p, until in self._failing_proxies.items() if now >= until]
        for p in expired:
            self._failing_proxies.pop(p, None)

        # Look for the first healthy proxy
        for _ in range(len(self._proxies)):
            proxy = self._proxies[self._index % len(self._proxies)]
            self._index += 1
            if proxy not in self._failing_proxies:
                return proxy

        # If all proxies are currently in cooldown, return least recently failed one
        return self._proxies[self._index % len(self._proxies)]

    def report_proxy_failure(self, proxy: Optional[str], reason: str = "error") -> None:
        """Mark a proxy as temporarily failing."""
        if not proxy:
            return
        self._failing_proxies[proxy] = time.time() + self._cooldown_seconds
        logger.warning("proxy_marked_failing", proxy=proxy[:25] + "...", reason=reason, cooldown_sec=self._cooldown_seconds)

    def report_proxy_success(self, proxy: Optional[str]) -> None:
        """Clear any failure record for a healthy proxy."""
        if proxy and proxy in self._failing_proxies:
            self._failing_proxies.pop(proxy, None)

    def create_client(
        self,
        *,
        timeout: Optional[float] = None,
        custom_headers: Optional[dict[str, str]] = None,
        force_direct: bool = False,
    ) -> httpx.AsyncClient:
        """Create an httpx.AsyncClient with proxy (if enabled) and browser headers."""
        settings = get_settings()
        timeout_val = timeout or settings.proxy_timeout_seconds
        headers = self.get_default_headers(custom_headers)

        proxy = None
        if not force_direct and settings.proxy_rotation_enabled:
            proxy = self.get_next_proxy()

        return httpx.AsyncClient(
            proxy=proxy,
            timeout=httpx.Timeout(timeout_val, connect=10.0),
            headers=headers,
            follow_redirects=True,
        )

    async def execute_with_retry(
        self,
        request_fn: Callable[[httpx.AsyncClient], Coroutine[Any, Any, httpx.Response]],
        *,
        max_retries: Optional[int] = None,
        custom_headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        """Execute an async request with proxy rotation and exponential backoff + jitter."""
        settings = get_settings()
        retries = max_retries if max_retries is not None else settings.proxy_max_retries
        backoff_factor = settings.proxy_backoff_factor

        last_exc: Optional[Exception] = None
        current_proxy: Optional[str] = None

        for attempt in range(1, retries + 1):
            client = self.create_client(custom_headers=custom_headers)
            current_proxy = str(client._transport._pool._proxy.url) if getattr(client._transport, "_pool", None) and getattr(client._transport._pool, "_proxy", None) else None
            try:
                async with client:
                    response = await request_fn(client)

                    # Handle Rate Limit (HTTP 429)
                    if response.status_code == 429:
                        self.report_proxy_failure(current_proxy, reason="rate_limited_429")
                        if attempt < retries:
                            # Exponential backoff with random jitter (e.g. 1.5s, 3.2s, etc.)
                            delay = (backoff_factor ** attempt) + random.uniform(0.5, 1.5)
                            logger.info("scraper_rate_limit_backoff", attempt=attempt, delay=round(delay, 2))
                            await asyncio.sleep(delay)
                            continue

                    if response.is_success or response.status_code in {301, 302, 304, 404}:
                        self.report_proxy_success(current_proxy)
                        return response

                    return response
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ProxyError) as exc:
                last_exc = exc
                self.report_proxy_failure(current_proxy, reason=type(exc).__name__)
                if attempt < retries:
                    delay = (backoff_factor ** attempt) + random.uniform(0.3, 1.0)
                    await asyncio.sleep(delay)
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    await asyncio.sleep(1.0)

        if last_exc:
            raise last_exc
        raise httpx.RequestError(f"Request failed after {retries} retry attempts")


proxy_pool = ProxyPoolManager()
