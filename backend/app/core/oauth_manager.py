"""Token manager for platform discovery and connected social accounts.

App-only token exchange is used only where the provider supports it. User or
page OAuth credentials are loaded from the encrypted Social Accounts store for
endpoints that require account context.
"""

import base64
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.redis import get_redis
from app.modules.social_media.security import decrypt_secret, encrypt_secret

logger = structlog.get_logger()


class OAuthTokenManager:
    """Handles OAuth 2.0 client credentials token lifecycle and caching."""

    def __init__(self) -> None:
        self.settings = get_settings()

    async def _read_cached_token(self, cache_key: str) -> Optional[str]:
        """Read an encrypted short-lived provider token from Redis.

        Tokens written by older versions were plaintext. They are deleted on
        read instead of being returned, forcing a safe refresh.
        """
        try:
            redis = await get_redis()
            cached = await redis.get(cache_key)
            if not cached:
                return None
            try:
                return decrypt_secret(str(cached))
            except Exception:
                await redis.delete(cache_key)
        except Exception:
            pass
        return None

    async def _write_cached_token(self, cache_key: str, token: str, ttl: int) -> None:
        """Cache a provider token only in encrypted form."""
        try:
            redis = await get_redis()
            await redis.setex(cache_key, ttl, encrypt_secret(token))
        except Exception as exc:
            logger.warning("oauth_token_cache_unavailable", cache_key=cache_key, error=type(exc).__name__)

    async def _get_db_source_config(self, platform: str) -> Optional[dict[str, Any]]:
        """Fetch platform configuration dynamically from database."""
        try:
            from app.core.database import get_celery_task_session
            from app.modules.trend_sources.models import TrendSource

            async with get_celery_task_session() as session:
                stmt = select(TrendSource).where(TrendSource.platform == platform).where(TrendSource.deleted_at.is_(None))
                res = await session.execute(stmt)
                source = res.scalar_one_or_none()
                if source and source.configuration:
                    return source.configuration
        except Exception:
            pass
        return None

    async def _get_connected_social_credential(self, platform: str) -> Optional[dict[str, Any]]:
        """Load the active encrypted OAuth credential created by Social Accounts."""
        try:
            from app.core.database import get_celery_task_session
            from app.modules.social_media.models import SocialConnection, SocialCredential
            from app.modules.social_media.security import decrypt_secret

            async with get_celery_task_session() as session:
                stmt = (
                    select(SocialConnection)
                    .where(SocialConnection.platform == platform)
                    .where(SocialConnection.status == "connected")
                    .where(SocialConnection.credential_ref.is_not(None))
                    .where(SocialConnection.deleted_at.is_(None))
                    .order_by(SocialConnection.updated_at.desc())
                )
                connections = (await session.execute(stmt)).scalars().all()

                for connection in connections:
                    try:
                        credential_id = uuid.UUID(str(connection.credential_ref))
                    except (ValueError, AttributeError, TypeError):
                        continue

                    credential = await session.get(SocialCredential, credential_id)
                    if not credential or credential.status != "active":
                        continue
                    if credential.expires_at and credential.expires_at <= datetime.now(timezone.utc):
                        continue

                    try:
                        access_token = decrypt_secret(credential.encrypted_access_token)
                    except Exception as exc:
                        logger.warning(
                            "social_credential_decrypt_failed",
                            platform=platform,
                            connection_id=str(connection.id),
                            error=str(exc),
                        )
                        continue

                    if access_token:
                        return {
                            "access_token": access_token,
                            "account_id": connection.account_id,
                            "metadata": connection.metadata_ or {},
                            "scopes": credential.scopes or connection.scopes or [],
                        }
        except Exception as exc:
            # Optional social tables must not stop Google/public fallback.
            logger.warning("social_credential_lookup_failed", platform=platform, error=str(exc))
        return None

    async def get_meta_context(self) -> Optional[dict[str, Any]]:
        """Return a connected Meta token together with the Instagram account ID."""
        connected = await self._get_connected_social_credential("instagram")
        if connected:
            return connected

        db_config = await self._get_db_source_config("instagram")
        static_token = (db_config and db_config.get("access_token")) or self.settings.instagram_access_token
        if not static_token:
            return None

        return {
            "access_token": static_token,
            "account_id": (db_config or {}).get("instagram_user_id") or (db_config or {}).get("account_id"),
            "metadata": {},
            "scopes": [],
        }

    async def get_meta_token(self) -> Optional[str]:
        """Get an Instagram-capable Meta user/page token.

        App credentials alone are intentionally not exchanged here: an app
        token does not provide the Instagram account context required by the
        hashtag/media endpoints used by the collector.
        """
        context = await self.get_meta_context()
        return context.get("access_token") if context else None

    async def get_tiktok_token(self) -> Optional[str]:
        """Get an active TikTok for Developers / Research API Access Token."""
        db_config = await self._get_db_source_config("tiktok")

        static_token = (db_config and db_config.get("access_token")) or self.settings.tiktok_access_token
        if static_token:
            return static_token

        configured_key, configured_secret = self.settings.tiktok_client_credentials
        client_key = (db_config and (db_config.get("client_key") or db_config.get("client_id"))) or configured_key
        client_secret = (db_config and db_config.get("client_secret")) or configured_secret

        if not client_key or not client_secret:
            return None

        cache_key = f"oauth:token:tiktok:{client_key}"
        cached = await self._read_cached_token(cache_key)
        if cached:
            return cached

        try:
            url = "https://open.tiktokapis.com/v2/oauth/token/"
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            data = {
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, data=data)
                if res.status_code == 200:
                    payload = res.json()
                    access_token = payload.get("data", {}).get("access_token") or payload.get("access_token")
                    expires_in = payload.get("data", {}).get("expires_in") or payload.get("expires_in", 7200)

                    if access_token:
                        await self._write_cached_token(cache_key, access_token, max(int(expires_in) - 300, 1800))
                        logger.info("tiktok_oauth_token_refreshed", client_key=client_key)
                        return access_token
                else:
                    logger.warning("tiktok_oauth_token_failed", status_code=res.status_code)
        except Exception as e:
            logger.error("tiktok_oauth_request_error", error=str(e))

        return None

    async def get_x_token(self) -> Optional[str]:
        """Get an X app-only Bearer Token for public API reads.

        X OAuth 2.0 client ID/secret belongs to the user-context PKCE flow.
        App-only token exchange must use the app API key/secret pair, so the
        two credential families are deliberately not interchangeable here.
        """
        db_config = await self._get_db_source_config("x")

        static_token = (db_config and (db_config.get("bearer_token") or db_config.get("access_token"))) or self.settings.x_bearer_token
        if static_token:
            return static_token

        api_key = (db_config and db_config.get("api_key")) or self.settings.x_api_key
        api_secret = (db_config and (db_config.get("api_secret") or db_config.get("api_key_secret"))) or self.settings.x_api_secret

        if not api_key or not api_secret:
            return None

        cache_key = f"oauth:token:x:{api_key}"
        cached = await self._read_cached_token(cache_key)
        if cached:
            return cached

        try:
            url = "https://api.twitter.com/oauth2/token"
            credentials = f"{api_key}:{api_secret}".encode("utf-8")
            encoded_credentials = base64.b64encode(credentials).decode("utf-8")
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            }
            data = {"grant_type": "client_credentials"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, headers=headers, data=data)
                if res.status_code == 200:
                    payload = res.json()
                    access_token = payload.get("access_token")
                    expires_in = payload.get("expires_in", 3600 * 24 * 180)

                    if access_token:
                        await self._write_cached_token(cache_key, access_token, max(int(expires_in) - 300, 3600))
                        logger.info("x_oauth_token_refreshed")
                        return access_token
                else:
                    logger.warning("x_oauth_token_failed", status_code=res.status_code)
        except Exception as e:
            logger.error("x_oauth_request_error", error=str(e))

        return None

    async def get_linkedin_token(self) -> Optional[str]:
        """Get a LinkedIn member token for identity requests.

        Client credentials identify the application but do not authorize
        ``/v2/userinfo`` on behalf of a LinkedIn member.
        """
        connected = await self._get_connected_social_credential("linkedin")
        if connected:
            return connected["access_token"]

        db_config = await self._get_db_source_config("linkedin")

        static_token = (db_config and db_config.get("access_token"))
        if static_token:
            return static_token
        return None

    def is_meta_configured(self) -> bool:
        return bool(
            (self.settings.meta_client_id and self.settings.meta_client_secret)
            or (self.settings.meta_app_id and self.settings.meta_app_secret)
            or self.settings.instagram_access_token
        )

    def is_tiktok_configured(self) -> bool:
        client_key, client_secret = self.settings.tiktok_client_credentials
        return bool(
            (client_key and client_secret)
            or self.settings.tiktok_access_token
        )

    def is_x_configured(self) -> bool:
        return bool(
            (self.settings.x_api_key and self.settings.x_api_secret)
            or self.settings.x_bearer_token
        )

    def is_linkedin_configured(self) -> bool:
        return bool(self.settings.linkedin_client_id and self.settings.linkedin_client_secret)


oauth_token_manager = OAuthTokenManager()
