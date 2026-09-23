"""Permanent public storage for generated trend reference images."""

from __future__ import annotations

import hashlib
import uuid
from pathlib import PurePosixPath

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceException
from app.modules.ai.services.image_generation import GeneratedImage
from app.modules.social_media.services.media_assets import SupabaseStorageClient
from app.modules.social_media.services.media_fetch import download_public_media


IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_REFERENCE_IMAGE_BYTES = 10 * 1024 * 1024


class TrendReferenceImageService:
    """Persist provider output without replacing or deleting earlier previews."""

    def __init__(self, storage: SupabaseStorageClient | None = None) -> None:
        self.storage = storage or SupabaseStorageClient()
        self.settings = get_settings()

    async def store(
        self,
        *,
        trend_id: uuid.UUID,
        prompt_package_id: uuid.UUID,
        generated: GeneratedImage,
    ) -> str:
        if not self.storage.configured:
            raise ExternalServiceException(message="Supabase Storage is not configured")

        if generated.image_bytes is not None:
            content = generated.image_bytes
            mime_type = generated.mime_type or "image/jpeg"
        elif generated.image_url:
            content, mime_type = await download_public_media(
                generated.image_url,
                MAX_REFERENCE_IMAGE_BYTES,
            )
        else:
            raise ExternalServiceException(message="Image provider returned no image content")

        normalized_mime = mime_type.lower().split(";", 1)[0]
        extension = IMAGE_EXTENSIONS.get(normalized_mime)
        if extension is None:
            raise ExternalServiceException(message=f"Unsupported reference image type '{normalized_mime}'")
        if not content or len(content) > MAX_REFERENCE_IMAGE_BYTES:
            raise ExternalServiceException(message="Reference image must be between 1 byte and 10 MB")

        checksum = hashlib.sha256(content).hexdigest()
        filename = f"{checksum[:16]}-{uuid.uuid4().hex[:12]}{extension}"
        path = str(PurePosixPath("trends", str(trend_id), str(prompt_package_id), filename))
        bucket = self.settings.supabase_trend_reference_bucket
        await self.storage.upload(
            bucket=bucket,
            path=path,
            content=content,
            mime_type=normalized_mime,
        )
        return self.storage.create_public_url(bucket=bucket, path=path)


trend_reference_image_service = TrendReferenceImageService()
