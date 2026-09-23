"""Social Media AI Agent API."""

import uuid
from urllib.parse import urlencode

import httpx
import structlog
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status
from fastapi.responses import PlainTextResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import accepted_response, success_response
from app.core.config import get_settings
from app.core.database import get_db
from app.core.exceptions import BadRequestException
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.auth.enums import UserRole
from app.modules.auth.models import User
from app.modules.social_media.dependencies import get_social_media_service
from app.modules.social_media.enums import CampaignStatus
from app.modules.social_media.schemas import (
    ApproveContentRequest,
    CampaignDecisionRequest,
    CreateContentBriefRequest,
    CreateCampaignRequest,
    ReschedulePublishJobRequest,
    ScheduleContentRequest,
    SocialOAuthDiagnosticsResponse,
    UpdateBrandKitRequest,
    UpdateContentVariantRequest,
)
from app.modules.social_media.services import SocialMediaService
from app.modules.social_media.services.connections import OAuthConnectionError
from app.modules.social_media.models import SocialMediaAsset
from app.modules.social_media.services.media_assets import media_asset_service
from app.modules.social_media.services.webhooks import (
    parse_instagram_event,
    summarize_instagram_event,
    verify_instagram_challenge,
    verify_instagram_signature,
)

router = APIRouter(prefix="/social", tags=["Social Media AI Agent"])
logger = structlog.get_logger()

MAX_MEDIA_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_INSTAGRAM_WEBHOOK_BYTES = 1024 * 1024
MAX_THREADS_LIFECYCLE_BYTES = 64 * 1024


@router.post("/briefs", status_code=status.HTTP_202_ACCEPTED)
async def create_social_brief(
    data: CreateContentBriefRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    result = await service.create_brief(data, created_by=current_user.id)
    return accepted_response(data=result.model_dump(), message="Social content brief queued")


@router.get("/briefs")
async def list_social_briefs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_briefs(page=page, page_size=page_size)
    result["items"] = [item.model_dump() for item in result["items"]]
    return success_response(data=result)


@router.get("/briefs/{brief_id}")
async def get_social_brief(
    brief_id: uuid.UUID,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.get_brief(brief_id)
    return success_response(data=result.model_dump())


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_social_campaign(
    data: CreateCampaignRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.create_campaign(data, created_by=current_user.id)
    return success_response(data=result.model_dump(), message="Campaign draft created")


@router.get("/campaigns")
async def list_social_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    campaign_status: str | None = Query(default=None, alias="status"),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_campaigns(page=page, page_size=page_size, status=campaign_status)
    return success_response(data=result)


@router.get("/campaigns/{campaign_id}")
async def get_social_campaign(
    campaign_id: uuid.UUID,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.get_campaign(campaign_id)
    return success_response(data=result.model_dump())


@router.post("/campaigns/{campaign_id}/submit")
async def submit_social_campaign(
    campaign_id: uuid.UUID,
    data: CampaignDecisionRequest | None = None,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.transition_campaign(
        campaign_id,
        target_status=CampaignStatus.PENDING_APPROVAL,
        actor_id=None,
        notes=data.notes if data else None,
    )
    return success_response(data=result.model_dump(), message="Campaign submitted for approval")


@router.post("/campaigns/{campaign_id}/approve")
async def approve_social_campaign(
    campaign_id: uuid.UUID,
    data: CampaignDecisionRequest | None = None,
    service: SocialMediaService = Depends(get_social_media_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.transition_campaign(
        campaign_id,
        target_status=CampaignStatus.APPROVED,
        actor_id=current_user.id,
        notes=data.notes if data else None,
    )
    return success_response(data=result.model_dump(), message="Campaign budget approved")


@router.post("/campaigns/{campaign_id}/reject")
async def reject_social_campaign(
    campaign_id: uuid.UUID,
    data: CampaignDecisionRequest | None = None,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.transition_campaign(
        campaign_id,
        target_status=CampaignStatus.REJECTED,
        actor_id=None,
        notes=data.notes if data else None,
    )
    return success_response(data=result.model_dump(), message="Campaign rejected")


@router.get("/content")
async def list_social_content(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    content_status: str | None = Query(default=None, alias="status"),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_content(page=page, page_size=page_size, status=content_status)
    result["items"] = [item.model_dump() for item in result["items"]]
    return success_response(data=result)


@router.get("/publish-jobs")
async def list_social_publish_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    publish_status: str | None = Query(default=None, alias="status"),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_publish_jobs(page=page, page_size=page_size, status=publish_status)
    result["items"] = [item.model_dump() for item in result["items"]]
    return success_response(data=result)


@router.get("/analytics")
async def list_social_analytics(
    limit: int = Query(default=100, ge=1, le=500),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_analytics(limit=limit)
    return success_response(data=[item.model_dump() for item in result])


@router.get("/optimization/insights")
async def list_social_performance_insights(
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_performance_insights()
    return success_response(data=[item.model_dump() for item in result])


@router.post("/optimization/analyze")
async def analyze_social_performance(
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.analyze_performance()
    return success_response(
        data=[item.model_dump() for item in result],
        message="Social performance insights refreshed",
    )


@router.get("/brand-kit")
async def get_social_brand_kit(
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.get_brand_kit()
    return success_response(data=result.model_dump())


@router.put("/brand-kit")
async def update_social_brand_kit(
    data: UpdateBrandKitRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await service.update_brand_kit(data)
    return success_response(data=result.model_dump(), message="Brand Brain updated")


@router.post("/assets", status_code=status.HTTP_201_CREATED)
async def upload_social_media_asset(
    file: UploadFile = File(...),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    content = await file.read(MAX_MEDIA_UPLOAD_BYTES + 1)
    if len(content) > MAX_MEDIA_UPLOAD_BYTES:
        raise BadRequestException(message="Media asset must not exceed 50 MB")
    result = await service.upload_media_asset(
        content=content,
        mime_type=file.content_type or "application/octet-stream",
        source_name=file.filename,
    )
    return success_response(data=result.model_dump(), message="Media asset uploaded")


@router.get("/assets")
async def list_social_media_assets(
    limit: int = Query(default=100, ge=1, le=500),
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_media_assets(limit=limit)
    return success_response(data=[item.model_dump() for item in result])


@router.post("/assets/{asset_id}/signed-url")
async def refresh_social_media_asset_url(
    asset_id: uuid.UUID,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.get_media_asset_url(asset_id)
    return success_response(data=result.model_dump())


@router.get("/assets/{asset_id}/public", include_in_schema=False)
async def serve_public_social_media_asset(
    asset_id: uuid.UUID,
    expires: int = Query(..., ge=1),
    signature: str = Query(..., min_length=64, max_length=128),
    db: AsyncSession = Depends(get_db),
):
    """Serve a ready public asset from our verified first-party domain.

    TikTok's photo PULL_FROM_URL flow validates URL ownership. This endpoint
    intentionally has no user dependency because provider crawlers cannot
    authenticate; access is limited to opaque asset IDs and ready assets.
    """
    if not media_asset_service.verify_public_proxy_signature(
        asset_id,
        expires_at=expires,
        signature=signature,
    ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    result = await db.execute(
        select(SocialMediaAsset)
        .where(SocialMediaAsset.id == asset_id)
        .where(SocialMediaAsset.status == "ready")
        .where(SocialMediaAsset.deleted_at.is_(None))
    )
    asset = result.scalar_one_or_none()
    if not asset:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    # Keep the provider-facing URL on our verified domain, but fetch the
    # object through a short-lived Supabase signed URL.  The bucket may be
    # private in an existing project even when new deployments request a
    # public bucket; TikTok must not depend on that project-level setting.
    source_url = await media_asset_service.storage.create_signed_url(
        bucket=asset.storage_bucket,
        path=asset.storage_path,
        expires_in=3600,
    )
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            upstream = await client.get(source_url)
    except httpx.HTTPError:
        return Response(status_code=status.HTTP_502_BAD_GATEWAY)
    if not upstream.is_success or len(upstream.content) > MAX_MEDIA_UPLOAD_BYTES:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    return Response(
        content=upstream.content,
        media_type=asset.mime_type or "application/octet-stream",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/connections")
async def list_social_connections(
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(get_current_user),
):
    result = await service.list_connection_catalog()
    return success_response(data=[item.model_dump() for item in result])


@router.post("/connections/{platform}/begin")
async def begin_social_connection(
    platform: str,
    service: SocialMediaService = Depends(get_social_media_service),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await service.begin_connection(platform, created_by=current_user.id)
    return success_response(data=result.model_dump(), message=result.message)


@router.get("/connections/diagnostics")
async def get_social_oauth_diagnostics(
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN)),
):
    result: SocialOAuthDiagnosticsResponse = service.get_oauth_diagnostics()
    return success_response(data=result.model_dump())


@router.get("/webhooks/instagram", response_class=PlainTextResponse)
async def verify_instagram_webhook(
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    """Complete Meta's public webhook subscription handshake."""
    expected_token = get_settings().instagram_webhook_verify_token
    if not expected_token:
        logger.error("instagram_webhook_not_configured")
        return PlainTextResponse("Webhook verification is not configured", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if not challenge or not verify_instagram_challenge(
        mode=mode,
        provided_token=verify_token,
        expected_token=expected_token,
    ):
        logger.warning("instagram_webhook_verification_rejected")
        return PlainTextResponse("Forbidden", status_code=status.HTTP_403_FORBIDDEN)
    logger.info("instagram_webhook_verified")
    return PlainTextResponse(challenge, status_code=status.HTTP_200_OK)


@router.post("/webhooks/instagram", response_class=PlainTextResponse)
async def receive_instagram_webhook(request: Request):
    """Authenticate and acknowledge an Instagram webhook event."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_INSTAGRAM_WEBHOOK_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    body = await request.body()
    if len(body) > MAX_INSTAGRAM_WEBHOOK_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    app_secret = get_settings().instagram_app_secret
    if not app_secret:
        logger.error("instagram_webhook_signature_not_configured")
        return PlainTextResponse("Webhook signature verification is not configured", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    if not verify_instagram_signature(
        body=body,
        signature=request.headers.get("x-hub-signature-256"),
        app_secret=app_secret,
    ):
        logger.warning("instagram_webhook_signature_rejected")
        return PlainTextResponse("Invalid signature", status_code=status.HTTP_403_FORBIDDEN)

    payload = parse_instagram_event(body)
    if payload is None:
        return PlainTextResponse("Invalid JSON payload", status_code=status.HTTP_400_BAD_REQUEST)

    logger.info("instagram_webhook_received", **summarize_instagram_event(payload))
    return PlainTextResponse("EVENT_RECEIVED", status_code=status.HTTP_200_OK)


async def _threads_uninstall_callback(request: Request):
    """Acknowledge Threads app deauthorization callbacks."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_THREADS_LIFECYCLE_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    if request.method == "POST" and len(await request.body()) > MAX_THREADS_LIFECYCLE_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    logger.info("threads_uninstall_callback_received", method=request.method)
    return PlainTextResponse("OK", status_code=status.HTTP_200_OK)


@router.get("/webhooks/threads/uninstall", response_class=PlainTextResponse, include_in_schema=False)
async def threads_uninstall_callback_get(request: Request):
    return await _threads_uninstall_callback(request)


@router.post("/webhooks/threads/uninstall", response_class=PlainTextResponse)
async def threads_uninstall_callback(request: Request):
    return await _threads_uninstall_callback(request)


async def _threads_remove_callback(request: Request):
    """Return the public data-deletion instructions required by Meta."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_THREADS_LIFECYCLE_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    if request.method == "POST" and len(await request.body()) > MAX_THREADS_LIFECYCLE_BYTES:
        return PlainTextResponse("Payload too large", status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    logger.info("threads_remove_callback_received", method=request.method)
    return {
        "url": "https://bookmind.my.id/data-deletion",
        "confirmation_code": "BOOKMIND-THREADS-DATA-DELETION",
    }


@router.get("/webhooks/threads/remove", include_in_schema=False)
async def threads_remove_callback_get(request: Request):
    return await _threads_remove_callback(request)


@router.post("/webhooks/threads/remove")
async def threads_remove_callback(request: Request):
    return await _threads_remove_callback(request)


@router.get("/connections/oauth/callback")
async def social_oauth_callback(
    state: str | None = None,
    code: str | None = None,
    error: str | None = None,
    service: SocialMediaService = Depends(get_social_media_service),
):
    settings = get_settings()
    try:
        if not state:
            raise OAuthConnectionError(
                reason="invalid_state",
                message="OAuth state is missing",
            )
        await service.complete_connection(state=state, code=code, error=error)
        query = urlencode({"connection": "success"})
    except OAuthConnectionError as exc:
        # Do not log the authorization code or full state value.
        logger.warning(
            "social_oauth_callback_failed",
            reason=exc.reason,
            platform=exc.platform,
            cause_type=type(exc.__cause__).__name__ if exc.__cause__ else None,
        )
        query_data = {"connection": "error", "reason": exc.reason}
        if exc.platform:
            query_data["platform"] = exc.platform
        query = urlencode(query_data)
    except Exception as exc:
        logger.exception("social_oauth_callback_unexpected", exception_type=type(exc).__name__)
        query = urlencode({"connection": "error", "reason": "connection_failed"})
    destination = f"{settings.social_frontend_base_url.rstrip('/')}/social/accounts?{query}"
    return RedirectResponse(url=destination, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/content/{content_id}/approve")
@router.post("/content/{content_id}/review")
async def review_social_content(
    content_id: uuid.UUID,
    data: ApproveContentRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    result = await service.review_content(content_id, data, reviewer_id=current_user.id)
    return success_response(data=result.model_dump(), message=f"Social content {data.decision.value}d")


@router.post("/content/{content_id}/schedule")
async def schedule_social_content(
    content_id: uuid.UUID,
    data: ScheduleContentRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    result = await service.schedule_content(content_id, data)
    return accepted_response(
        data=[job.model_dump() for job in result],
        message="Social content scheduling queued",
    )


@router.patch("/variants/{variant_id}")
async def update_social_variant(
    variant_id: uuid.UUID,
    data: UpdateContentVariantRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    result = await service.update_variant(variant_id, data)
    return success_response(data=result.model_dump(), message="Social variant updated and revalidated")


@router.post("/publish-jobs/{job_id}/cancel")
async def cancel_social_publish_job(
    job_id: uuid.UUID,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.cancel_publish_job(job_id)
    return success_response(data=result.model_dump(), message="Social publish job cancelled")


@router.post("/publish-jobs/{job_id}/retry")
async def retry_social_publish_job(
    job_id: uuid.UUID,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.retry_publish_job(job_id)
    return accepted_response(data=result.model_dump(), message="Social publish job queued for retry")


@router.post("/publish-jobs/{job_id}/reschedule")
async def reschedule_social_publish_job(
    job_id: uuid.UUID,
    data: ReschedulePublishJobRequest,
    service: SocialMediaService = Depends(get_social_media_service),
    _user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.reschedule_publish_job(job_id, data)
    return accepted_response(data=result.model_dump(), message="Social publish job rescheduled")
