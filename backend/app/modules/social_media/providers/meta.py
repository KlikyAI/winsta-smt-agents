"""Meta Graph API adapter for Instagram Professional and Facebook Pages."""

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException


class MetaGraphClient:
    """Small fail-closed client for Meta OAuth, publishing, and metrics."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.version = self.settings.meta_graph_api_version
        self.graph_base = f"https://graph.facebook.com/{self.version}"

    @property
    def app_id(self) -> str | None:
        return self.settings.meta_app_id or self.settings.meta_client_id

    @property
    def app_secret(self) -> str | None:
        return self.settings.meta_app_secret or self.settings.meta_client_secret

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str]) -> str:
        if not self.app_id or not self.app_secret:
            raise ExternalServiceException(message="Meta OAuth credentials are not configured")
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        if self.settings.meta_login_config_id:
            # Facebook Login for Business configurations own their permission
            # set. This integration uses a User Access Token configuration:
            # `config_id` replaces `scope`, and Meta's default response type is
            # already `code`. The system-user-only
            # `override_default_response_type` parameter must not be included.
            params["config_id"] = self.settings.meta_login_config_id
        else:
            # Legacy Facebook Login applications without a Business Login
            # configuration still receive their permissions through `scope`.
            params["response_type"] = "code"
            params["scope"] = ",".join(scopes)
        return f"https://www.facebook.com/{self.version}/dialog/oauth?{urlencode(params)}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> dict[str, Any]:
        if not self.app_id or not self.app_secret:
            raise ExternalServiceException(message="Meta OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/oauth/access_token",
                params={
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
            )
        payload = self._payload_or_error(response, "Meta authorization code exchange failed")
        if not payload.get("access_token"):
            raise ExternalServiceException(message="Meta did not return an access token")
        expires_at = None
        if payload.get("expires"):
            expires_at = datetime.now(timezone.utc).timestamp() + int(payload["expires"])
        return {**payload, "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc) if expires_at else None}

    async def refresh_long_lived_token(self, access_token: str) -> dict[str, Any]:
        if not self.app_id or not self.app_secret:
            raise ExternalServiceException(message="Meta OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.app_id,
                    "client_secret": self.app_secret,
                    "fb_exchange_token": access_token,
                },
            )
        payload = self._payload_or_error(response, "Meta token refresh failed")
        if not payload.get("access_token"):
            raise ExternalServiceException(message="Meta did not return an access token")
        expires_at = None
        if payload.get("expires_in") or payload.get("expires"):
            exp = int(payload.get("expires_in") or payload.get("expires"))
            expires_at = datetime.now(timezone.utc).timestamp() + exp
        return {**payload, "expires_at": datetime.fromtimestamp(expires_at, tz=timezone.utc) if expires_at else None}

    async def list_pages(self, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/me/accounts",
                params={
                    "fields": "id,name,access_token,instagram_business_account",
                    "access_token": access_token,
                },
            )
        payload = self._payload_or_error(response, "Meta did not return manageable Pages")
        return payload.get("data", [])

    async def list_granted_permissions(self, access_token: str) -> list[str]:
        """Return only permissions Meta reports as granted for the user token."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/me/permissions",
                params={"access_token": access_token},
            )
        payload = self._payload_or_error(response, "Meta did not return granted permissions")
        return sorted(
            {
                item["permission"]
                for item in payload.get("data", [])
                if item.get("status") == "granted" and item.get("permission")
            }
        )

    async def publish(self, *, platform: str, account_id: str, page_id: str | None, access_token: str, media_url: str, caption: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            if platform == "instagram":
                container = await client.post(
                    f"{self.graph_base}/{account_id}/media",
                    params={"image_url": media_url, "caption": caption, "access_token": access_token},
                )
                container_payload = self._payload_or_error(container, "Meta failed to create the Instagram media container")
                publish = await client.post(
                    f"{self.graph_base}/{account_id}/media_publish",
                    params={"creation_id": container_payload["id"], "access_token": access_token},
                )
                return self._payload_or_error(publish, "Meta failed to publish the Instagram media")

            if platform == "facebook" and page_id:
                response = await client.post(
                    f"{self.graph_base}/{page_id}/photos",
                    params={"url": media_url, "caption": caption, "published": "true", "access_token": access_token},
                )
                return self._payload_or_error(response, "Meta failed to publish the Facebook photo")

        raise ExternalServiceException(message=f"Meta publisher does not support platform '{platform}'")

    async def fetch_metrics(self, *, platform: str, external_post_id: str, access_token: str) -> dict[str, Any]:
        metrics = (
            "likes,comments,shares,saved,reach,impressions"
            if platform == "instagram"
            else "post_impressions,post_engaged_users,post_reactions_by_type_total"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_base}/{external_post_id}/insights",
                params={"metric": metrics, "access_token": access_token},
            )
        payload = self._payload_or_error(response, "Meta failed to fetch post insights")
        return self._normalize_metrics(payload)

    @staticmethod
    def _normalize_metrics(payload: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for metric in payload.get("data", []):
            values = metric.get("values") or []
            normalized[metric.get("name", "unknown")] = values[-1].get("value") if values else metric.get("value")
        return normalized

    @staticmethod
    def _payload_or_error(response: httpx.Response, message: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalServiceException(message=message) from exc
        if not response.is_success or payload.get("error"):
            raise ExternalServiceException(message=f"{message}: HTTP {response.status_code}")
        return payload
