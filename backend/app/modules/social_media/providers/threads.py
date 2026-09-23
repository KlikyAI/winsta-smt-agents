"""Threads API publishing adapter."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.exceptions import ExternalServiceException
from app.modules.social_media.providers.contracts import PublishContext, PublishResult, SocialPublisherAdapter


class ThreadsPublisherAdapter(SocialPublisherAdapter):
    """Publish text or image posts through the official Threads API."""

    platforms = frozenset({"threads"})
    requires_media = False
    api_endpoint = "https://graph.threads.net"

    @staticmethod
    def _payload(response: httpx.Response, message: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceException(message=f"{message}: invalid provider response") from exc
        error = payload.get("error")
        if not response.is_success or error:
            raise ExternalServiceException(message=f"{message}: HTTP {response.status_code}")
        return payload

    @staticmethod
    def _media_type(media_url: str | None) -> str:
        if not media_url:
            return "TEXT"
        path = media_url.lower().split("?", 1)[0]
        return "VIDEO" if path.endswith((".mp4", ".mov", ".webm")) else "IMAGE"

    async def publish(self, context: PublishContext) -> PublishResult:
        media_type = self._media_type(context.media_url)
        params: dict[str, Any] = {
            "text": context.caption[:500],
            "media_type": media_type,
            "access_token": context.access_token,
        }
        if media_type == "IMAGE":
            params["image_url"] = context.media_url
        elif media_type == "VIDEO":
            params["video_url"] = context.media_url

        async with httpx.AsyncClient(timeout=90.0) as client:
            container_response = await client.post(f"{self.api_endpoint}/me/threads", params=params)
            container = self._payload(container_response, "Threads media container creation failed")
            container_id = container.get("id") or container.get("creation_id")
            if not container_id:
                raise ExternalServiceException(message="Threads returned no media container ID")
            publish_response = await client.post(
                f"{self.api_endpoint}/me/threads_publish",
                params={"creation_id": str(container_id), "access_token": context.access_token},
            )
        published = self._payload(publish_response, "Threads post publishing failed")
        post_id = published.get("id") or published.get("media_id")
        if not post_id:
            raise ExternalServiceException(message="Threads returned no post ID")
        return PublishResult(
            external_post_id=str(post_id),
            response_data={"provider": "threads", "raw": published},
        )

    async def fetch_metrics(
        self,
        *,
        platform: str,
        external_post_id: str,
        access_token: str,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_endpoint}/{external_post_id}",
                params={
                    "fields": "views,likes,replies,reposts,quotes",
                    "access_token": access_token,
                },
            )
        payload = self._payload(response, "Threads metrics lookup failed")
        return {
            key: payload[key]
            for key in ("views", "likes", "replies", "reposts", "quotes")
            if key in payload
        }
