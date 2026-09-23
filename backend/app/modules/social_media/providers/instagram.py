"""Instagram Graph API adapter for accounts connected through Instagram Login."""

import asyncio
import time
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException


class InstagramGraphClient:
    """Direct Instagram API client; intentionally separate from Facebook Pages API."""

    graph_base = "https://graph.instagram.com"

    def __init__(self) -> None:
        self.settings = get_settings()

    @staticmethod
    def _payload_or_error(response: httpx.Response, message: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceException(message=f"{message}: invalid response") from exc
        if not response.is_success or payload.get("error"):
            raise ExternalServiceException(message=f"{message}: HTTP {response.status_code}")
        return payload

    async def _wait_for_container(
        self,
        client: httpx.AsyncClient,
        *,
        container_id: str,
        access_token: str,
        max_wait_seconds: float = 90.0,
    ) -> None:
        """Wait until Instagram finishes processing the media container.

        Instagram can return a container ID before the media is ready for
        ``media_publish``. Publishing immediately in that window produces the
        opaque ``Media ID is not available`` error. Images are usually quick,
        but polling also makes this safe for slower uploads and API retries.
        """
        deadline = time.monotonic() + max_wait_seconds
        while True:
            status_response = await client.get(
                f"{self.graph_base}/{container_id}",
                params={"fields": "status_code", "access_token": access_token},
            )
            status_payload = self._payload_or_error(
                status_response, "Instagram failed to check media container status"
            )
            status = str(
                status_payload.get("status_code") or status_payload.get("status") or ""
            ).upper()

            # Some API versions omit status for image containers. In that case
            # the publish endpoint remains the source of truth.
            if not status or status in {"FINISHED", "PUBLISHED"}:
                return
            if status in {"ERROR", "EXPIRED"}:
                detail = status_payload.get("status") or status
                raise ExternalServiceException(
                    message=f"Instagram media container failed: {detail}"
                )
            if time.monotonic() >= deadline:
                raise ExternalServiceException(
                    message="Instagram media container did not finish processing in time"
                )
            await asyncio.sleep(2.0)

    async def publish(self, *, account_id: str, access_token: str, media_url: str, caption: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            container_response = await client.post(
                f"{self.graph_base}/{account_id}/media",
                params={"image_url": media_url, "caption": caption, "access_token": access_token},
            )
            container = self._payload_or_error(container_response, "Instagram failed to create the media container")
            container_id = container.get("id") or container.get("creation_id") or container.get("media_id")
            if not container_id:
                keys = ", ".join(sorted(str(key) for key in container.keys())) or "none"
                raise ExternalServiceException(
                    message=f"Instagram media container response did not include an ID (keys: {keys})"
                )
            await self._wait_for_container(
                client,
                container_id=str(container_id),
                access_token=access_token,
            )
            publish_response = await client.post(
                f"{self.graph_base}/{account_id}/media_publish",
                params={"creation_id": str(container_id), "access_token": access_token},
            )
        published = self._payload_or_error(publish_response, "Instagram failed to publish the media")
        if not published.get("id") and published.get("media_id"):
            published["id"] = published["media_id"]
        return published

    async def fetch_metrics(self, *, external_post_id: str, access_token: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/{external_post_id}",
                params={"fields": "like_count,comments_count", "access_token": access_token},
            )
        payload = self._payload_or_error(response, "Instagram failed to fetch media metrics")
        return {key: payload[key] for key in ("like_count", "comments_count") if key in payload}
