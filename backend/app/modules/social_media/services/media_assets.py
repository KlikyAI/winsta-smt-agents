"""Supabase-backed durable media assets for social publishing."""

from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import quote

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.modules.social_media.models import SocialMediaAsset
from app.modules.social_media.services.media_fetch import download_public_media


ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
}
MAX_ASSET_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class StoredMedia:
    asset: SocialMediaAsset
    signed_url: str
    deduplicated: bool


class SupabaseStorageClient:
    """Minimal server-only client for the Supabase Storage REST API."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def key(self) -> str | None:
        return self.settings.supabase_secret_key or self.settings.supabase_service_role_key

    @property
    def configured(self) -> bool:
        return bool(self.settings.supabase_url and self.key and self.settings.supabase_storage_bucket)

    def _headers(self) -> dict[str, str]:
        if not self.configured:
            raise ExternalServiceException(
                message="Supabase Storage requires SUPABASE_URL and SUPABASE_SECRET_KEY"
            )
        return {"apikey": self.key or "", "Authorization": f"Bearer {self.key}"}

    def _object_path(self, bucket: str, path: str) -> str:
        safe_path = quote(path, safe="/")
        return f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{safe_path}"

    async def upload(self, *, bucket: str, path: str, content: bytes, mime_type: str) -> None:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                self._object_path(bucket, path),
                headers={
                    **self._headers(),
                    "Content-Type": mime_type,
                    "Cache-Control": "31536000, immutable",
                    "x-upsert": "false",
                },
                content=content,
            )
        if not response.is_success:
            raise ExternalServiceException(
                message=f"Supabase Storage upload failed: HTTP {response.status_code} {response.text[:300]}"
            )

    async def create_signed_url(self, *, bucket: str, path: str, expires_in: int | None = None) -> str:
        ttl = expires_in or self.settings.supabase_signed_url_ttl_seconds
        safe_path = quote(path, safe="/")
        endpoint = (
            f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/sign/"
            f"{bucket}/{safe_path}"
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                endpoint,
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"expiresIn": ttl},
            )
        if not response.is_success:
            raise ExternalServiceException(
                message=f"Supabase signed URL creation failed: HTTP {response.status_code}"
            )
        payload = response.json()
        signed = payload.get("signedURL") or payload.get("signedUrl")
        if not signed:
            raise ExternalServiceException(message="Supabase returned no signed URL")
        return self._absolute_signed_url(signed)

    def _absolute_signed_url(self, signed: str) -> str:
        if signed.startswith("http://") or signed.startswith("https://"):
            return signed
        if signed.startswith("/object/"):
            signed = f"/storage/v1{signed}"
        return f"{self.settings.supabase_url.rstrip('/')}{signed}"

    def create_public_url(self, *, bucket: str, path: str) -> str:
        """Build the stable public URL for an object in a public bucket."""
        if not self.settings.supabase_url:
            raise ExternalServiceException(message="Supabase Storage is not configured")
        safe_path = quote(path, safe="/")
        return (
            f"{self.settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
            f"{bucket}/{safe_path}"
        )


class MediaAssetService:
    def __init__(self, storage: SupabaseStorageClient | None = None) -> None:
        self.storage = storage or SupabaseStorageClient()

    @property
    def configured(self) -> bool:
        return self.storage.configured

    async def store_remote(
        self,
        session: AsyncSession,
        *,
        organization_id: uuid.UUID,
        source_url: str,
        content_item_id: uuid.UUID | None = None,
        provider: str | None = None,
        prompt: str | None = None,
        aspect_ratio: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        content, mime_type = await download_public_media(source_url, MAX_ASSET_BYTES)
        return await self.store_bytes(
            session,
            organization_id=organization_id,
            content=content,
            mime_type=mime_type,
            source_url=source_url,
            content_item_id=content_item_id,
            provider=provider,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            metadata=metadata,
        )

    async def store_bytes(
        self,
        session: AsyncSession,
        *,
        organization_id: uuid.UUID,
        content: bytes,
        mime_type: str,
        source_url: str | None = None,
        content_item_id: uuid.UUID | None = None,
        provider: str | None = None,
        prompt: str | None = None,
        aspect_ratio: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StoredMedia:
        if not self.configured:
            raise ExternalServiceException(message="Supabase Storage is not configured")
        normalized_mime = mime_type.lower().split(";")[0]
        extension = ALLOWED_MIME_TYPES.get(normalized_mime)
        if not extension:
            raise ExternalServiceException(message=f"Unsupported media type '{normalized_mime}'")
        if not content or len(content) > MAX_ASSET_BYTES:
            raise ExternalServiceException(message="Media must be between 1 byte and 50 MB")

        checksum = hashlib.sha256(content).hexdigest()
        existing_result = await session.execute(
            select(SocialMediaAsset)
            .where(SocialMediaAsset.organization_id == organization_id)
            .where(SocialMediaAsset.sha256 == checksum)
            .where(SocialMediaAsset.status == "ready")
            .where(SocialMediaAsset.deleted_at.is_(None))
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            return StoredMedia(
                asset=existing,
                signed_url=await self.signed_url(existing),
                deduplicated=True,
            )

        bucket = self.storage.settings.supabase_storage_bucket
        date_path = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        filename = f"{checksum[:16]}-{uuid.uuid4().hex[:12]}{extension}"
        storage_path = str(PurePosixPath(str(organization_id), date_path, filename))
        await self.storage.upload(
            bucket=bucket,
            path=storage_path,
            content=content,
            mime_type=normalized_mime,
        )
        asset = SocialMediaAsset(
            organization_id=organization_id,
            content_item_id=content_item_id,
            storage_bucket=bucket,
            storage_path=storage_path,
            source_url=source_url,
            mime_type=normalized_mime,
            media_type="video" if normalized_mime.startswith("video/") else "image",
            size_bytes=len(content),
            sha256=checksum,
            provider=provider,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            status="ready",
            metadata_=metadata or {},
        )
        session.add(asset)
        await session.flush()
        return StoredMedia(
            asset=asset,
            signed_url=await self.signed_url(asset),
            deduplicated=False,
        )

    async def signed_url(self, asset: SocialMediaAsset, *, expires_in: int | None = None) -> str:
        return await self.storage.create_signed_url(
            bucket=asset.storage_bucket,
            path=asset.storage_path,
            expires_in=expires_in,
        )

    def public_proxy_url(self, asset: SocialMediaAsset, *, expires_in: int = 21600) -> str:
        """Return a short-lived, asset-scoped URL for provider media crawlers."""
        base_url = get_settings().social_oauth_callback_base_url.rstrip("/")
        expires_at = int(time.time()) + max(60, min(expires_in, 86400))
        payload = f"{asset.id}:{expires_at}".encode()
        secret = (get_settings().social_token_encryption_key or "").encode()
        signature = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        return f"{base_url}/api/v1/social/assets/{asset.id}/public?expires={expires_at}&signature={signature}"

    @staticmethod
    def verify_public_proxy_signature(
        asset_id: uuid.UUID,
        *,
        expires_at: int,
        signature: str,
    ) -> bool:
        if expires_at < int(time.time()) or not signature:
            return False
        secret = (get_settings().social_token_encryption_key or "").encode()
        expected = hmac.new(
            secret,
            f"{asset_id}:{expires_at}".encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


media_asset_service = MediaAssetService()
