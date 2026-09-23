"""Celery tasks for Social Media AI Agent workflows."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.database import get_celery_task_session
from app.modules.social_media.enums import ContentBriefStatus, ContentItemStatus, PublishJobStatus
from app.modules.social_media.models import (
    BrandKit,
    ContentBrief,
    ContentItem,
    ContentVariant,
    PublishJob,
    SocialConnection,
    SocialCredential,
    SocialMetricSnapshot,
    SocialMediaAsset,
)
from app.modules.ai.services.image_generation import image_generation_service
from app.modules.social_media.providers import (
    PublishContext,
    PublisherUnavailableError,
    publisher_registry,
)
from app.modules.social_media.providers.meta import MetaGraphClient
from app.modules.social_media.providers.oauth import get_oauth_client
from app.modules.social_media.security import decrypt_secret, encrypt_secret
from app.modules.social_media.services.generation import generate_ai_platform_variant, run_variant_qa
from app.modules.social_media.services.media_assets import media_asset_service
from app.modules.social_media.services.media_fetch import download_public_media
from app.modules.social_media.services.performance import refresh_performance_insights
from app.modules.social_media.services.youtube_video import youtube_video_renderer
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


def _is_non_retryable_provider_error(exc: Exception) -> bool:
    """Return true for provider errors that cannot improve by retrying."""
    message = str(exc).lower()
    return (
        "credits depleted" in message
        or '"status":402' in message
        # TikTok blocks Direct Post for unaudited clients regardless of the
        # selected privacy level; retrying cannot change that policy state.
        or "unaudited_client_can_only_post_to_private_accounts" in message
    )


async def _generate_social_content(brief_id: str) -> dict:
    async with get_celery_task_session() as session:
        brief_uuid = uuid.UUID(brief_id)
        result = await session.execute(
            select(ContentBrief)
            .options(selectinload(ContentBrief.content_items))
            .where(ContentBrief.id == brief_uuid)
            .where(ContentBrief.deleted_at.is_(None))
        )
        brief = result.scalar_one_or_none()
        if brief is None:
            return {"brief_id": brief_id, "stage": "not_found"}
        if brief.content_items:
            return {
                "brief_id": brief_id,
                "stage": "already_generated",
                "content_item_id": str(brief.content_items[0].id),
            }

        brand_result = await session.execute(
            select(BrandKit)
            .where(BrandKit.organization_id == brief.organization_id)
            .where(BrandKit.is_active.is_(True))
            .where(BrandKit.deleted_at.is_(None))
            .order_by(BrandKit.version.desc(), BrandKit.updated_at.desc())
            .limit(1)
        )
        brand_kit = brand_result.scalar_one_or_none()
        brand_context = {
            "version": brand_kit.version,
            "brand_name": brand_kit.brand_name,
            "tagline": brand_kit.tagline,
            "colors": brand_kit.colors or {},
            "fonts": brand_kit.fonts or {},
            "tone": brand_kit.tone,
            "target_audience": brand_kit.target_audience,
            "default_hashtags": brand_kit.default_hashtags or [],
            "disclaimer": brand_kit.disclaimer,
            "forbidden_terms": brand_kit.forbidden_terms or [],
            "required_terms": brand_kit.required_terms or [],
            "product_facts": brand_kit.product_facts or {},
            "languages": brand_kit.languages or ["id", "en", "ar"],
            "guidelines": brand_kit.guidelines,
        } if brand_kit else {}

        try:
            brief.status = ContentBriefStatus.GENERATING.value
            await session.flush()

            item = ContentItem(
                organization_id=brief.organization_id,
                brief_id=brief.id,
                concept=brief.title,
                status=ContentItemStatus.QA_PENDING.value,
                ai_provider="winsta-structured-generator",
                ai_model="social-copy-v1",
                content_data={
                    "generation_mode": "deterministic",
                    "source": "manual_brief" if not brief.source_trend_id else "approved_trend",
                    "objective": brief.objective,
                },
            )
            session.add(item)
            await session.flush()

            all_passed = True
            variants: list[ContentVariant] = []
            media_cache: dict[str, tuple[str | None, uuid.UUID | None, dict]] = {}
            for platform in brief.target_platforms:
                for language in (brief.target_languages or [brief.language]):
                    generated = await generate_ai_platform_variant(
                        title=brief.title,
                        objective=brief.objective,
                        audience=brief.target_audience,
                        tone=brief.tone,
                        language=language,
                        platform=platform,
                        media_url=(brief.brief_data or {}).get("media_url"),
                        brand_context=brand_context,
                    )
                    source_media = generated.get("media_ref")
                    generated_image_bytes: bytes | None = None
                    generated_image_mime: str | None = None
                    # YouTube needs its own video asset. Keep image assets shared
                    # for the other channels, but never let a rendered MP4 leak
                    # into an Instagram/TikTok variant through the cache.
                    cache_scope = platform if platform == "youtube" else "visual"
                    cache_key = (
                        f"{cache_scope}:source:{source_media}"
                        if source_media
                        else f"{cache_scope}:generated:{generated['aspect_ratio']}"
                    )
                    media_asset_id = None
                    if cache_key in media_cache:
                        cached_url, media_asset_id, cached_metadata = media_cache[cache_key]
                        generated["media_ref"] = cached_url
                        generated["generation_metadata"]["image"] = cached_metadata
                    elif source_media or (brief.brief_data or {}).get("generate_image", True):
                        image_metadata: dict = {"source": "provided"}
                        if not source_media:
                            image = await image_generation_service.generate(
                                prompt=(brief.brief_data or {}).get("visual_prompt") or generated["visual_prompt"],
                                aspect_ratio=generated["aspect_ratio"],
                                model=(brief.brief_data or {}).get("image_model", "flux-realism"),
                            )
                            source_media = image.image_url
                            generated_image_bytes = image.image_bytes
                            generated_image_mime = image.mime_type
                            image_metadata = image.model_dump()
                        generated["media_ref"] = source_media
                        if (source_media or generated_image_bytes) and media_asset_service.configured:
                            try:
                                if generated_image_bytes:
                                    stored = await media_asset_service.store_bytes(
                                        session,
                                        organization_id=brief.organization_id,
                                        content=generated_image_bytes,
                                        mime_type=generated_image_mime or "image/jpeg",
                                        content_item_id=item.id,
                                        provider=image_metadata.get("provider") or "provided",
                                        prompt=generated["visual_prompt"],
                                        aspect_ratio=generated["aspect_ratio"],
                                        metadata={
                                            "platform": platform,
                                            "language": language,
                                            "generation": image_metadata,
                                        },
                                    )
                                else:
                                    stored = await media_asset_service.store_remote(
                                        session,
                                        organization_id=brief.organization_id,
                                        content_item_id=item.id,
                                        source_url=source_media,
                                        provider=image_metadata.get("provider") or "provided",
                                        prompt=generated["visual_prompt"],
                                        aspect_ratio=generated["aspect_ratio"],
                                        metadata={
                                            "platform": platform,
                                            "language": language,
                                            "generation": image_metadata,
                                        },
                                    )
                                generated["media_ref"] = stored.signed_url
                                media_asset_id = stored.asset.id
                                image_metadata["storage"] = {
                                    "asset_id": str(stored.asset.id),
                                    "bucket": stored.asset.storage_bucket,
                                    "path": stored.asset.storage_path,
                                    "deduplicated": stored.deduplicated,
                                }
                            except Exception as exc:
                                logger.warning(
                                    "social_media_asset_mirror_failed",
                                    brief_id=brief_id,
                                    platform=platform,
                                    error=str(exc),
                                )
                                image_metadata["storage"] = {"status": "fallback_source_url"}
                        generated["generation_metadata"]["image"] = image_metadata
                        media_cache[cache_key] = (
                            generated.get("media_ref"),
                            media_asset_id,
                            image_metadata,
                        )
                    if platform == "youtube" and generated.get("media_ref") and media_asset_service.configured:
                        try:
                            current_asset = (
                                await session.get(SocialMediaAsset, media_asset_id)
                                if media_asset_id
                                else None
                            )
                            # User-provided MP4 files are already valid YouTube
                            # media. Images (including generated AI images) are
                            # rendered into a short vertical MP4.
                            if not current_asset or current_asset.media_type != "video":
                                if generated_image_bytes:
                                    source_bytes = generated_image_bytes
                                    source_mime = generated_image_mime or "image/jpeg"
                                else:
                                    source_bytes, source_mime = await download_public_media(
                                        str(generated["media_ref"]),
                                        max_bytes=50 * 1024 * 1024,
                                    )
                                if source_mime == "video/mp4":
                                    # A remote MP4 may not have been mirrored
                                    # when storage is unavailable; keep it as-is.
                                    pass
                                else:
                                    rendered = await youtube_video_renderer.render_from_bytes(
                                        source_bytes,
                                        extension={
                                            "image/jpeg": ".jpg",
                                            "image/png": ".png",
                                            "image/webp": ".webp",
                                        }.get(source_mime, ".jpg"),
                                    )
                                    video_metadata = {
                                        "renderer": "ffmpeg-still-to-short-v1",
                                        "duration_seconds": youtube_video_renderer.duration_seconds,
                                        "width": youtube_video_renderer.width,
                                        "height": youtube_video_renderer.height,
                                        "source_asset_id": str(media_asset_id) if media_asset_id else None,
                                    }
                                    stored_video = await media_asset_service.store_bytes(
                                        session,
                                        organization_id=brief.organization_id,
                                        content=rendered,
                                        mime_type="video/mp4",
                                        source_url=str(generated["media_ref"]),
                                        content_item_id=item.id,
                                        provider="youtube-video-renderer",
                                        prompt=generated["visual_prompt"],
                                        aspect_ratio="9:16",
                                        metadata=video_metadata,
                                    )
                                    generated["media_ref"] = stored_video.signed_url
                                    media_asset_id = stored_video.asset.id
                                    generated["generation_metadata"]["video"] = video_metadata
                                    media_cache[cache_key] = (
                                        generated["media_ref"],
                                        media_asset_id,
                                        image_metadata,
                                    )
                        except Exception as exc:
                            logger.warning(
                                "youtube_video_render_failed",
                                brief_id=brief_id,
                                platform=platform,
                                error=str(exc),
                            )
                    qa_result = run_variant_qa(generated, brand_context)
                    qa_passed = qa_result["status"] == "passed"
                    all_passed = all_passed and qa_passed
                    variants.append(
                        ContentVariant(
                            content_item_id=item.id,
                            media_asset_id=media_asset_id,
                            platform=generated["platform"],
                            language=generated["language"],
                            format=generated["format"],
                            aspect_ratio=generated["aspect_ratio"],
                            caption=generated["caption"],
                            hook=generated["hook"],
                            cta=generated["cta"],
                            hashtags=generated["hashtags"],
                            media_ref=generated["media_ref"],
                            visual_prompt=generated["visual_prompt"],
                            generation_metadata=generated["generation_metadata"],
                            version=generated["version"],
                            qa_status=qa_result["status"],
                            qa_result=qa_result,
                            status=generated["status"],
                        )
                    )
            ai_variants = [
                variant for variant in variants
                if (variant.generation_metadata or {}).get("mode") == "ai"
            ]
            if ai_variants:
                metadata = ai_variants[0].generation_metadata or {}
                item.ai_provider = metadata.get("provider")
                item.ai_model = metadata.get("model")
                item.content_data = {**(item.content_data or {}), "generation_mode": "ai_with_fallback"}
            session.add_all(variants)
            item.status = (
                ContentItemStatus.READY_FOR_APPROVAL.value
                if all_passed
                else ContentItemStatus.FAILED.value
            )
            brief.status = (
                ContentBriefStatus.READY_FOR_REVIEW.value
                if all_passed
                else ContentBriefStatus.FAILED.value
            )
            await session.commit()
            logger.info(
                "social_content_generation_completed",
                brief_id=brief_id,
                content_item_id=str(item.id),
                variants=len(variants),
                qa_passed=all_passed,
            )
            return {
                "brief_id": brief_id,
                "content_item_id": str(item.id),
                "stage": brief.status,
                "variants": len(variants),
            }
        except Exception as exc:
            await session.rollback()
            failed_brief = await session.get(ContentBrief, brief_uuid)
            if failed_brief:
                failed_brief.status = ContentBriefStatus.FAILED.value
                await session.commit()
            logger.exception("social_content_generation_failed", brief_id=brief_id, error=str(exc))
            raise


@celery_app.task(name="app.workers.social_tasks.generate_social_content")
def generate_social_content(brief_id: str) -> dict:
    """Generate, validate, and persist reviewable social content variants."""
    logger.info("social_content_generation_started", brief_id=brief_id)
    return asyncio.run(_generate_social_content(brief_id))


async def _publish_social_job(publish_job_id: str) -> dict:
    async with get_celery_task_session() as session:
        job_uuid = uuid.UUID(publish_job_id)
        result = await session.execute(
            select(PublishJob)
            .options(
                selectinload(PublishJob.content_variant)
                .selectinload(ContentVariant.content_item)
                .selectinload(ContentItem.variants)
            )
            .where(PublishJob.id == job_uuid)
            .where(PublishJob.deleted_at.is_(None))
        )
        job = result.scalar_one_or_none()
        if job is None:
            return {"publish_job_id": publish_job_id, "stage": "not_found"}
        if job.status == PublishJobStatus.PUBLISHED.value:
            return {"publish_job_id": publish_job_id, "stage": "already_published"}
        if job.status == PublishJobStatus.CANCELLED.value:
            return {"publish_job_id": publish_job_id, "stage": "cancelled"}
        if job.status == PublishJobStatus.PUBLISHING.value:
            return {"publish_job_id": publish_job_id, "stage": "already_publishing"}
        now = datetime.now(timezone.utc)
        if job.scheduled_at and job.scheduled_at > now:
            job.status = PublishJobStatus.SCHEDULED.value
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": "scheduled"}
        if job.attempt_count >= job.max_attempts:
            job.status = PublishJobStatus.FAILED.value
            job.error = "Maximum publishing attempts reached. Retry manually after resolving the error."
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "max_attempts_reached"}

        connection_result = await session.execute(
            select(SocialConnection)
            .where(SocialConnection.organization_id == job.organization_id)
            .where(SocialConnection.platform == job.platform)
            .where(SocialConnection.status == "connected")
            .where(SocialConnection.deleted_at.is_(None))
            .limit(1)
        )
        connection = connection_result.scalar_one_or_none()
        job.attempt_count += 1
        job.last_attempt_at = now

        if connection is None:
            job.status = PublishJobStatus.CONNECTION_REQUIRED.value
            job.error = f"Connect an authorized {job.platform} account before publishing."
            reason = "account_not_connected"
            job.response_data = {"reason": reason, "safe_to_retry": True}
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": reason}

        try:
            adapter = publisher_registry.get(job.platform)
        except PublisherUnavailableError:
            job.status = PublishJobStatus.CONNECTION_REQUIRED.value
            job.error = f"The {job.platform} publishing adapter is not active yet."
            job.response_data = {"reason": "publisher_adapter_pending", "safe_to_retry": True}
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "publisher_adapter_pending"}

        variant = job.content_variant
        media_url = variant.media_ref if variant else None
        if variant and variant.media_asset_id and media_asset_service.configured:
            try:
                asset = await session.get(SocialMediaAsset, variant.media_asset_id)
                if asset and asset.status == "ready":
                    # TikTok's PULL_FROM_URL requires a publicly reachable URL
                    # on a domain verified by the developer app. Serve the
                    # public Supabase object through our first-party host so
                    # bookmind.my.id can be verified in TikTok's portal.
                    media_url = (
                        media_asset_service.public_proxy_url(asset)
                        if job.platform == "tiktok"
                        else await media_asset_service.signed_url(asset, expires_in=21600)
                    )
                    variant.media_ref = media_url
            except Exception as exc:
                logger.warning(
                    "social_media_asset_signing_failed",
                    publish_job_id=publish_job_id,
                    asset_id=str(variant.media_asset_id),
                    error=str(exc),
                )
        if not variant or (adapter.requires_media and not media_url):
            job.status = PublishJobStatus.MEDIA_REQUIRED.value
            job.error = "Attach a publicly reachable image URL before publishing."
            job.response_data = {"reason": "media_required", "safe_to_retry": True}
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "media_required"}

        credential = None
        if connection.credential_ref:
            try:
                credential = await session.get(SocialCredential, uuid.UUID(connection.credential_ref))
            except ValueError:
                credential = None
        if not credential or credential.status != "active":
            job.status = PublishJobStatus.CONNECTION_REQUIRED.value
            job.error = "Reconnect the social account because its server credential is unavailable."
            job.response_data = {"reason": "credential_unavailable", "safe_to_retry": True}
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "credential_unavailable"}
        expected_provider = "meta" if job.platform == "facebook" else job.platform
        if credential.provider != expected_provider:
            job.status = PublishJobStatus.CONNECTION_REQUIRED.value
            job.error = f"Reconnect {job.platform}; this account uses an outdated authorization provider."
            job.response_data = {
                "reason": "provider_mismatch",
                "safe_to_retry": True,
            }
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "provider_mismatch"}
        access_token = decrypt_secret(credential.encrypted_access_token)
        token_expiring = (
            credential.expires_at
            and credential.expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        if token_expiring:
            if credential.provider == "meta":
                job.status = PublishJobStatus.CONNECTION_REQUIRED.value
                job.error = "Reconnect the social account because its authorization has expired."
                job.response_data = {"reason": "credential_expired", "safe_to_retry": True}
                await session.commit()
                return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "credential_expired"}
            if credential.provider not in {"instagram", "threads"} and not credential.encrypted_refresh_token:
                job.status = PublishJobStatus.CONNECTION_REQUIRED.value
                job.error = "Reconnect the social account because its authorization has expired."
                job.response_data = {"reason": "credential_expired", "safe_to_retry": True}
                await session.commit()
                return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "credential_expired"}
            try:
                refresh_value = access_token if credential.provider in {"instagram", "threads"} else decrypt_secret(credential.encrypted_refresh_token)
                refreshed = await get_oauth_client(credential.provider).refresh_token(refresh_value, credential.scopes or [])
                access_token = refreshed.access_token
                credential.encrypted_access_token = encrypt_secret(refreshed.access_token)
                if refreshed.refresh_token:
                    credential.encrypted_refresh_token = encrypt_secret(refreshed.refresh_token)
                credential.expires_at = refreshed.expires_at
                credential.scopes = refreshed.scopes or credential.scopes
                await session.commit()
            except Exception as exc:
                job.status = PublishJobStatus.CONNECTION_REQUIRED.value
                job.error = "The social authorization could not be refreshed; reconnect the account."
                job.response_data = {"reason": "token_refresh_failed", "safe_to_retry": True}
                await session.commit()
                logger.warning("social_token_refresh_failed", platform=job.platform, error=str(exc))
                return {"publish_job_id": publish_job_id, "stage": job.status, "reason": "token_refresh_failed"}

        job.status = PublishJobStatus.PUBLISHING.value
        job.error = None
        await session.commit()
        try:
            result = await adapter.publish(PublishContext(
                platform=job.platform,
                account_id=connection.account_id,
                account_metadata=connection.metadata_ or {},
                access_token=access_token,
                media_url=media_url,
                caption=variant.caption or "",
                language=variant.language,
                idempotency_key=job.idempotency_key,
            ))
            job.status = PublishJobStatus.PUBLISHED.value
            job.external_post_id = result.external_post_id
            job.response_data = result.response_data
            job.next_attempt_at = None
            variant.status = ContentItemStatus.PUBLISHED.value
            sibling_statuses = {item.status for item in variant.content_item.variants}
            if sibling_statuses <= {ContentItemStatus.PUBLISHED.value}:
                variant.content_item.status = ContentItemStatus.PUBLISHED.value
            await session.commit()
            return {"publish_job_id": publish_job_id, "stage": job.status, "external_post_id": result.external_post_id}
        except Exception as exc:
            await session.rollback()
            failed_job = None
            failed_job = await session.get(PublishJob, job_uuid)
            if failed_job:
                retryable = (
                    failed_job.attempt_count < failed_job.max_attempts
                    and not _is_non_retryable_provider_error(exc)
                )
                failed_job.status = (
                    PublishJobStatus.SCHEDULED.value if retryable else PublishJobStatus.FAILED.value
                )
                failed_job.error = str(exc)[:1000]
                failed_job.next_attempt_at = (
                    datetime.now(timezone.utc) + timedelta(minutes=2 ** failed_job.attempt_count)
                    if retryable
                    else None
                )
                failed_job.response_data = {
                    "safe_to_retry": retryable,
                    "reason": "provider_quota_exhausted" if not retryable and _is_non_retryable_provider_error(exc) else None,
                }
                await session.commit()
            logger.exception("social_publish_failed", publish_job_id=publish_job_id, error=str(exc))
            return {"publish_job_id": publish_job_id, "stage": failed_job.status if failed_job else PublishJobStatus.FAILED.value}


async def _dispatch_due_social_jobs() -> dict:
    """Claim due jobs for delivery; safe to run from more than one beat process."""
    now = datetime.now(timezone.utc)
    async with get_celery_task_session() as session:
        result = await session.execute(
            select(PublishJob)
            .where(PublishJob.status.in_([
                PublishJobStatus.SCHEDULED.value,
                PublishJobStatus.QUEUED.value,
            ]))
            .where(PublishJob.attempt_count < PublishJob.max_attempts)
            .where(func.coalesce(PublishJob.next_attempt_at, PublishJob.scheduled_at) <= now)
            .where(PublishJob.deleted_at.is_(None))
            .order_by(PublishJob.scheduled_at.asc())
            .limit(100)
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars().all())
        for job in jobs:
            job.status = PublishJobStatus.QUEUED.value
            # A lost broker message becomes eligible for recovery after five minutes.
            job.next_attempt_at = now + timedelta(minutes=5)
        job_ids = [str(job.id) for job in jobs]
        await session.commit()

    for job_id in job_ids:
        publish_social_job.delay(job_id)
    return {"status": "completed", "jobs_dispatched": len(job_ids)}


@celery_app.task(name="app.workers.social_tasks.dispatch_due_social_jobs")
def dispatch_due_social_jobs() -> dict:
    return asyncio.run(_dispatch_due_social_jobs())


@celery_app.task(name="app.workers.social_tasks.publish_social_job")
def publish_social_job(publish_job_id: str) -> dict:
    """Attempt provider delivery and pause safely at unavailable boundaries."""
    logger.info("social_publish_started", publish_job_id=publish_job_id)
    return asyncio.run(_publish_social_job(publish_job_id))


@celery_app.task(name="app.workers.social_tasks.sync_social_analytics")
def sync_social_analytics() -> dict:
    """Fetch current metrics for published accounts with active credentials."""
    logger.info("social_analytics_sync_started")
    return asyncio.run(_sync_social_analytics())


async def _sync_social_analytics() -> dict:
    async with get_celery_task_session() as session:
        result = await session.execute(
            select(PublishJob)
            .options(selectinload(PublishJob.content_variant))
            .where(PublishJob.status == PublishJobStatus.PUBLISHED.value)
            .where(PublishJob.external_post_id.is_not(None))
            .where(PublishJob.deleted_at.is_(None))
            .order_by(PublishJob.updated_at.desc())
            .limit(100)
        )
        jobs = result.scalars().all()
        snapshots_created = 0
        organizations_updated: set[uuid.UUID] = set()
        for job in jobs:
            connection_result = await session.execute(
                select(SocialConnection)
                .where(SocialConnection.organization_id == job.organization_id)
                .where(SocialConnection.platform == job.platform)
                .where(SocialConnection.status == "connected")
                .where(SocialConnection.deleted_at.is_(None))
                .limit(1)
            )
            connection = connection_result.scalar_one_or_none()
            if not connection or not connection.credential_ref:
                continue
            try:
                credential = await session.get(SocialCredential, uuid.UUID(connection.credential_ref))
                if not credential or credential.status != "active":
                    continue
                adapter = publisher_registry.get(job.platform)
                metrics = await adapter.fetch_metrics(
                    platform=job.platform,
                    external_post_id=job.external_post_id,
                    access_token=decrypt_secret(credential.encrypted_access_token),
                )
                # TikTok returns a publish_id as soon as the upload is
                # initialized.  The actual photo download/publish happens
                # asynchronously, so an init response is not proof of
                # delivery. Reconcile terminal failures here so the queue
                # exposes the existing "Publish again" action instead of
                # leaving a failed post marked as published forever.
                if job.platform == "tiktok":
                    tiktok_status = str(metrics.get("status") or "").upper()
                    fail_reason = str(metrics.get("fail_reason") or "").strip()
                    if tiktok_status in {"FAILED", "PUBLISH_FAILED"} or fail_reason:
                        job.status = PublishJobStatus.FAILED.value
                        job.error = (
                            f"TikTok publish failed after initialization: {fail_reason}"
                            if fail_reason
                            else "TikTok publish failed after initialization."
                        )[:1000]
                        job.next_attempt_at = None
                        job.response_data = {
                            **(job.response_data or {}),
                            "tiktok_status": metrics,
                            "safe_to_retry": True,
                        }
                        if job.content_variant:
                            job.content_variant.status = ContentItemStatus.FAILED.value
                session.add(SocialMetricSnapshot(
                    organization_id=job.organization_id,
                    publish_job_id=job.id,
                    platform=job.platform,
                    external_post_id=job.external_post_id,
                    metrics=metrics,
                    captured_at=datetime.now(timezone.utc),
                ))
                snapshots_created += 1
                organizations_updated.add(job.organization_id)
            except Exception as exc:
                logger.warning("social_analytics_job_failed", publish_job_id=str(job.id), error=str(exc))
        await session.flush()
        insights_refreshed = 0
        for organization_id in organizations_updated:
            insights_refreshed += len(
                await refresh_performance_insights(session, organization_id)
            )
        await session.commit()
        return {
            "status": "completed",
            "jobs_checked": len(jobs),
            "snapshots_created": snapshots_created,
            "insights_refreshed": insights_refreshed,
        }


async def _refresh_expiring_social_tokens() -> dict:
    """Find active social credentials expiring within 24h and auto-refresh them."""
    async with get_celery_task_session() as session:
        threshold = datetime.now(timezone.utc) + timedelta(hours=24)
        result = await session.execute(
            select(SocialCredential)
            .where(SocialCredential.status == "active")
            .where(SocialCredential.expires_at.is_not(None))
            .where(SocialCredential.expires_at <= threshold)
            .where(SocialCredential.deleted_at.is_(None))
        )
        credentials = result.scalars().all()
        refreshed_count = 0
        failed_count = 0

        for credential in credentials:
            try:
                if credential.provider == "meta":
                    current_token = decrypt_secret(credential.encrypted_access_token)
                    refreshed = await MetaGraphClient().refresh_long_lived_token(current_token)
                    credential.encrypted_access_token = encrypt_secret(refreshed["access_token"])
                    if refreshed.get("expires_at"):
                        credential.expires_at = refreshed["expires_at"]
                    refreshed_count += 1
                    logger.info("social_token_auto_refreshed", credential_id=str(credential.id), provider="meta")
                elif credential.provider in {"instagram", "threads"} or credential.encrypted_refresh_token:
                    refresh_token_plain = (
                        decrypt_secret(credential.encrypted_refresh_token)
                        if credential.provider not in {"instagram", "threads"}
                        else decrypt_secret(credential.encrypted_access_token)
                    )
                    client = get_oauth_client(credential.provider)
                    token = await client.refresh_token(refresh_token_plain, credential.scopes or [])
                    credential.encrypted_access_token = encrypt_secret(token.access_token)
                    if token.refresh_token:
                        credential.encrypted_refresh_token = encrypt_secret(token.refresh_token)
                    if token.expires_at:
                        credential.expires_at = token.expires_at
                    refreshed_count += 1
                    logger.info("social_token_auto_refreshed", credential_id=str(credential.id), provider=credential.provider)
            except Exception as exc:
                failed_count += 1
                logger.warning(
                    "social_token_auto_refresh_failed",
                    credential_id=str(credential.id),
                    provider=credential.provider,
                    error=str(exc),
                )

        if refreshed_count > 0:
            await session.commit()

        return {
            "status": "completed",
            "checked_count": len(credentials),
            "refreshed_count": refreshed_count,
            "failed_count": failed_count,
        }


@celery_app.task(name="app.workers.social_tasks.refresh_expiring_social_tokens", bind=True, max_retries=3)
def refresh_expiring_social_tokens(self) -> dict:
    """Periodic Celery task for automatic OAuth token refreshment."""
    logger.info("refresh_expiring_social_tokens_start")
    try:
        return asyncio.run(_refresh_expiring_social_tokens())
    except Exception as exc:
        logger.error("refresh_expiring_social_tokens_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120)
