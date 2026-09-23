"""Safe bounded downloads for media that must be mirrored or uploaded."""

import asyncio
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import httpx

from app.core.exceptions import ExternalServiceException


async def download_public_media(
    url: str,
    max_bytes: int = 50 * 1024 * 1024,
) -> tuple[bytes, str]:
    current_url = url
    for _ in range(4):
        await _validate_public_url(current_url)
        chunks: list[bytes] = []
        size = 0
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=False) as client:
            async with client.stream(
                "GET",
                current_url,
                headers={"Accept": "image/*,video/mp4"},
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if not location:
                        raise ExternalServiceException(message="Media redirect has no destination")
                    current_url = urljoin(current_url, location)
                    continue
                if not response.is_success:
                    raise ExternalServiceException(
                        message=f"Could not download media: HTTP {response.status_code}"
                    )
                media_type = response.headers.get(
                    "content-type",
                    "application/octet-stream",
                ).split(";")[0]
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        raise ExternalServiceException(
                            message=f"Media exceeds the {max_bytes // (1024 * 1024)} MB limit"
                        )
                    chunks.append(chunk)
        return b"".join(chunks), media_type
    raise ExternalServiceException(message="Media URL exceeded the redirect limit")


async def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ExternalServiceException(message="Media URL must use public HTTP or HTTPS")

    default_port = 443 if parsed.scheme == "https" else 80
    addresses = await asyncio.to_thread(
        socket.getaddrinfo,
        parsed.hostname,
        parsed.port or default_port,
    )
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ExternalServiceException(message="Private or local media URLs are not allowed")
