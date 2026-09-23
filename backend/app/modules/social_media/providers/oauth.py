"""OAuth 2.0 clients for non-Meta social providers."""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException

logger = structlog.get_logger()


@dataclass(frozen=True)
class OAuthToken:
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    scopes: list[str]
    raw: dict[str, Any]


@dataclass(frozen=True)
class OAuthAccount:
    account_id: str
    account_name: str | None
    metadata: dict[str, Any]


def create_pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _token(payload: dict[str, Any], default_scopes: list[str]) -> OAuthToken:
    access_token = payload.get("access_token")
    if not access_token:
        raise ExternalServiceException(message="OAuth provider returned no access token")
    expires_at = None
    if payload.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(payload["expires_in"]))
    raw_scopes = payload.get("scope") or default_scopes
    scopes = raw_scopes.split() if isinstance(raw_scopes, str) else list(raw_scopes)
    return OAuthToken(
        access_token=access_token,
        refresh_token=payload.get("refresh_token"),
        expires_at=expires_at,
        scopes=scopes,
        raw=payload,
    )


def _json_or_error(response: httpx.Response, message: str) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ExternalServiceException(message=f"{message}: invalid response") from exc
    provider_error = payload.get("error")
    failed = not response.is_success or (
        isinstance(provider_error, dict) and provider_error.get("code") not in {None, "ok"}
    )
    if failed:
        # Keep provider diagnostics useful without logging response bodies,
        # authorization codes, access tokens, or error descriptions.
        error_code = provider_error.get("code") if isinstance(provider_error, dict) else provider_error
        logger.warning(
            "oauth_provider_request_rejected",
            provider_operation=message[:100],
            status_code=response.status_code,
            error_code=str(error_code)[:80] if error_code is not None else None,
        )
        # Preserve the provider's machine-readable code for the callback layer.
        # This is safe to expose (unlike response bodies, codes, or tokens) and
        # lets the UI distinguish an OAuth scope grant problem from a bad code.
        suffix = str(error_code)[:80] if error_code is not None else f"HTTP {response.status_code}"
        raise ExternalServiceException(message=f"{message}: {suffix}")
    return payload


def _instagram_token(payload: dict[str, Any], default_scopes: list[str]) -> OAuthToken:
    """Normalize Instagram Login token responses, including permission arrays."""
    permissions = payload.get("permissions")
    normalized = {**payload}
    if permissions and not normalized.get("scope"):
        normalized["scope"] = permissions
    return _token(normalized, default_scopes)


class InstagramOAuthClient:
    """Direct Instagram Login client (separate from Facebook Login for Business)."""

    platform = "instagram"
    authorization_endpoint = "https://www.instagram.com/oauth/authorize"
    short_token_endpoint = "https://api.instagram.com/oauth/access_token"
    graph_endpoint = "https://graph.instagram.com"

    def __init__(self) -> None:
        self.settings = get_settings()

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str], **_: Any) -> str:
        app_id = self.settings.instagram_app_id
        if not app_id:
            raise ExternalServiceException(message="Instagram OAuth credentials are not configured")
        return f"{self.authorization_endpoint}?" + urlencode({
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ",".join(scopes),
            "state": state,
        })

    async def exchange_code(self, *, code: str, redirect_uri: str, scopes: list[str], **_: Any) -> OAuthToken:
        if not self.settings.instagram_app_id or not self.settings.instagram_app_secret:
            raise ExternalServiceException(message="Instagram OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.short_token_endpoint, data={
                "client_id": self.settings.instagram_app_id,
                "client_secret": self.settings.instagram_app_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
                "code": code,
            })
            short_payload = _json_or_error(response, "Instagram authorization code exchange failed")
            short_token = short_payload.get("access_token")
            if not short_token:
                raise ExternalServiceException(message="Instagram returned no short-lived access token")
            long_response = await client.get(f"{self.graph_endpoint}/access_token", params={
                "grant_type": "ig_exchange_token",
                "client_secret": self.settings.instagram_app_secret,
                "access_token": short_token,
            })
        long_payload = _json_or_error(long_response, "Instagram long-lived token exchange failed")
        merged = {**short_payload, **long_payload}
        return _instagram_token(merged, scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.graph_endpoint}/refresh_access_token", params={
                "grant_type": "ig_refresh_token",
                "access_token": refresh_token,
            })
        return _instagram_token(_json_or_error(response, "Instagram token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.graph_endpoint}/me",
                params={
                    "fields": "id,username,name,profile_picture_url",
                    "access_token": access_token,
                },
            )
        account = _json_or_error(response, "Instagram account lookup failed")
        account_id = account.get("id")
        if not account_id:
            raise ExternalServiceException(message="Instagram returned no account ID")
        return OAuthAccount(
            str(account_id),
            account.get("name") or account.get("username"),
            {"username": account.get("username"), "profile_picture_url": account.get("profile_picture_url")},
        )


class ThreadsOAuthClient:
    """OAuth client for the official Threads API."""

    platform = "threads"
    authorization_endpoint = "https://threads.net/oauth/authorize"
    api_endpoint = "https://graph.threads.net"

    def __init__(self) -> None:
        self.settings = get_settings()

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str], **_: Any) -> str:
        app_id = self.settings.threads_app_id
        if not app_id:
            raise ExternalServiceException(message="Threads OAuth credentials are not configured")
        return f"{self.authorization_endpoint}?" + urlencode({
            "client_id": app_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(scopes),
            "response_type": "code",
            "state": state,
        })

    async def exchange_code(self, *, code: str, redirect_uri: str, scopes: list[str], **_: Any) -> OAuthToken:
        if not self.settings.threads_app_id or not self.settings.threads_app_secret:
            raise ExternalServiceException(message="Threads OAuth credentials are not configured")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.api_endpoint}/oauth/access_token",
                params={
                    "client_id": self.settings.threads_app_id,
                    "client_secret": self.settings.threads_app_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
            )
            short_payload = _json_or_error(response, "Threads authorization code exchange failed")
            short_token = short_payload.get("access_token")
            if not short_token:
                raise ExternalServiceException(message="Threads returned no short-lived access token")
            long_response = await client.get(
                f"{self.api_endpoint}/access_token",
                params={
                    "grant_type": "th_exchange_token",
                    "client_secret": self.settings.threads_app_secret,
                    "access_token": short_token,
                },
            )
        long_payload = _json_or_error(long_response, "Threads long-lived token exchange failed")
        return _token({**short_payload, **long_payload}, scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_endpoint}/refresh_access_token",
                params={"grant_type": "th_refresh_token", "access_token": refresh_token},
            )
        # The endpoint may return an empty 200 response while keeping the
        # token valid. Preserve it and extend the normal long-lived window.
        if response.status_code == 200 and not response.content:
            return OAuthToken(
                access_token=refresh_token,
                refresh_token=None,
                expires_at=datetime.now(timezone.utc) + timedelta(days=60),
                scopes=scopes,
                raw={},
            )
        return _token(_json_or_error(response, "Threads token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.api_endpoint}/me",
                params={
                    "fields": "id,username,name,threads_profile_picture_url",
                    "access_token": access_token,
                },
            )
        account = _json_or_error(response, "Threads account lookup failed")
        account_id = account.get("id")
        if not account_id:
            raise ExternalServiceException(message="Threads returned no account ID")
        return OAuthAccount(
            str(account_id),
            account.get("name") or account.get("username"),
            {
                "username": account.get("username"),
                "profile_picture_url": account.get("threads_profile_picture_url"),
            },
        )


class TikTokOAuthClient:
    platform = "tiktok"

    def __init__(self) -> None:
        self.settings = get_settings()

    def _client_credentials(self) -> tuple[str | None, str | None]:
        return self.settings.tiktok_client_credentials

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str], **_: Any) -> str:
        client_key, _ = self._client_credentials()
        params = {
            "client_key": client_key,
            "response_type": "code",
            "scope": ",".join(scopes),
            "redirect_uri": redirect_uri,
            "state": state,
            # TikTok otherwise reuses an existing login/grant and may skip
            # consent, leaving newly-added Sandbox scopes unauthorized.
            "disable_auto_auth": "1",
        }
        return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"

    async def exchange_code(self, *, code: str, redirect_uri: str, scopes: list[str], **_: Any) -> OAuthToken:
        client_key, client_secret = self._client_credentials()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://open.tiktokapis.com/v2/oauth/token/", data={
                "client_key": client_key,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            })
        return _token(_json_or_error(response, "TikTok token exchange failed"), scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        client_key, client_secret = self._client_credentials()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://open.tiktokapis.com/v2/oauth/token/", data={
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            })
        return _token(_json_or_error(response, "TikTok token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://open.tiktokapis.com/v2/user/info/",
                # Keep account linking within the baseline Login Kit scope.
                # username/profile fields require user.info.profile on newer
                # TikTok API versions and otherwise return scope_not_authorized.
                params={"fields": "open_id,union_id,avatar_url,display_name"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        user = _json_or_error(response, "TikTok account lookup failed").get("data", {}).get("user", {})
        account_id = user.get("open_id")
        if not account_id:
            raise ExternalServiceException(message="TikTok returned no account ID")
        return OAuthAccount(str(account_id), user.get("display_name") or user.get("username"), {})


class GoogleOAuthClient:
    platform = "youtube"

    def __init__(self) -> None:
        self.settings = get_settings()

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str], **_: Any) -> str:
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": self.settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        })

    async def exchange_code(self, *, code: str, redirect_uri: str, scopes: list[str], **_: Any) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            })
        return _token(_json_or_error(response, "Google token exchange failed"), scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://oauth2.googleapis.com/token", data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            })
        return _token(_json_or_error(response, "Google token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "id,snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        items = _json_or_error(response, "YouTube channel lookup failed").get("items", [])
        if not items:
            raise ExternalServiceException(message="Google returned no YouTube channel")
        channel = items[0]
        return OAuthAccount(str(channel["id"]), channel.get("snippet", {}).get("title"), {})


class XOAuthClient:
    platform = "x"

    def __init__(self) -> None:
        self.settings = get_settings()

    def authorization_url(
        self, *, state: str, redirect_uri: str, scopes: list[str], code_challenge: str, **_: Any
    ) -> str:
        return "https://x.com/i/oauth2/authorize?" + urlencode({
            "response_type": "code",
            "client_id": self.settings.x_client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })

    async def exchange_code(
        self, *, code: str, redirect_uri: str, scopes: list[str], code_verifier: str, **_: Any
    ) -> OAuthToken:
        auth = None
        if self.settings.x_client_secret:
            auth = httpx.BasicAuth(self.settings.x_client_id or "", self.settings.x_client_secret)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.x.com/2/oauth2/token", data={
                "client_id": self.settings.x_client_id,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }, auth=auth)
        return _token(_json_or_error(response, "X token exchange failed"), scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        auth = httpx.BasicAuth(self.settings.x_client_id or "", self.settings.x_client_secret or "")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.x.com/2/oauth2/token", data={
                "client_id": self.settings.x_client_id,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }, auth=auth)
        return _token(_json_or_error(response, "X token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.x.com/2/users/me",
                params={"user.fields": "name,username,profile_image_url"},
                headers={"Authorization": f"Bearer {access_token}"},
            )
        user = _json_or_error(response, "X account lookup failed").get("data", {})
        if not user.get("id"):
            raise ExternalServiceException(message="X returned no account ID")
        return OAuthAccount(str(user["id"]), user.get("name") or user.get("username"), {"username": user.get("username")})


class LinkedInOAuthClient:
    platform = "linkedin"

    def __init__(self) -> None:
        self.settings = get_settings()

    def authorization_url(self, *, state: str, redirect_uri: str, scopes: list[str], **_: Any) -> str:
        return "https://www.linkedin.com/oauth/v2/authorization?" + urlencode({
            "response_type": "code",
            "client_id": self.settings.linkedin_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(scopes),
        })

    async def exchange_code(self, *, code: str, redirect_uri: str, scopes: list[str], **_: Any) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.settings.linkedin_client_id,
                "client_secret": self.settings.linkedin_client_secret,
                "redirect_uri": redirect_uri,
            })
        return _token(_json_or_error(response, "LinkedIn token exchange failed"), scopes)

    async def refresh_token(self, refresh_token: str, scopes: list[str]) -> OAuthToken:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://www.linkedin.com/oauth/v2/accessToken", data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.settings.linkedin_client_id,
                "client_secret": self.settings.linkedin_client_secret,
            })
        return _token(_json_or_error(response, "LinkedIn token refresh failed"), scopes)

    async def get_account(self, access_token: str) -> OAuthAccount:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        user = _json_or_error(response, "LinkedIn account lookup failed")
        if not user.get("sub"):
            raise ExternalServiceException(message="LinkedIn returned no account ID")
        return OAuthAccount(str(user["sub"]), user.get("name"), {})


def get_oauth_client(platform: str):
    clients = {
        "instagram": InstagramOAuthClient,
        "threads": ThreadsOAuthClient,
        "tiktok": TikTokOAuthClient,
        "youtube": GoogleOAuthClient,
        "x": XOAuthClient,
        "linkedin": LinkedInOAuthClient,
    }
    client_class = clients.get(platform)
    if not client_class:
        raise ExternalServiceException(message=f"OAuth is not supported for '{platform}'")
    return client_class()
