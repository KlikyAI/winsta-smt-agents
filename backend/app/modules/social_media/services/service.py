"""Application service for the Social Media AI Agent foundation."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
import secrets
from typing import Any

import structlog
from sqlalchemy import select

from app.core.config import get_settings
from app.core.exceptions import BadRequestException, ConflictException, ExternalServiceException, NotFoundException
from app.modules.social_media.enums import CampaignStatus, ContentBriefStatus, ContentItemStatus, PublishJobStatus
from app.modules.social_media.models import (
    BrandKit,
    ContentBrief,
    ContentApproval,
    ContentVariant,
    PublishJob,
    SocialConnection,
    SocialCredential,
    SocialCampaign,
    SocialMetricSnapshot,
    SocialPerformanceInsight,
    SocialMediaAsset,
    SocialOAuthState,
)
from app.modules.social_media.repositories import (
    SocialBriefRepository,
    SocialCampaignRepository,
    SocialConnectionRepository,
    SocialContentRepository,
    SocialOrganizationRepository,
    SocialPublishJobRepository,
)
from app.modules.social_media.schemas import (
    ApproveContentRequest,
    BeginSocialConnectionResponse,
    BrandKitResponse,
    ContentBriefResponse,
    ContentItemResponse,
    CreateContentBriefRequest,
    PublishJobResponse,
    ReschedulePublishJobRequest,
    ScheduleContentRequest,
    SocialBriefQueuedResponse,
    SocialCampaignResponse,
    CreateCampaignRequest,
    SocialConnectionAccountResponse,
    SocialContentQueueItemResponse,
    SocialPublishQueueItemResponse,
    SocialPlatformConnectionResponse,
    SocialOAuthDiagnosticsResponse,
    SocialMetricSnapshotResponse,
    SocialPerformanceInsightResponse,
    SocialMediaAssetResponse,
    UpdateContentVariantRequest,
    UpdateBrandKitRequest,
)
from app.modules.social_media.services.connections import (
    PROVIDER_SPECS,
    callback_url,
    get_provider_spec,
    missing_provider_settings,
    oauth_diagnostics,
    OAuthConnectionError,
    requested_scopes,
)
from app.modules.social_media.providers import MetaGraphClient
from app.modules.social_media.providers.oauth import create_pkce_pair, get_oauth_client
from app.modules.social_media.security import encrypt_secret, hash_state
from app.modules.social_media.services.brand_kit import SocialBrandKitService
from app.modules.social_media.services.campaigns import SocialCampaignService
from app.modules.social_media.services.generation import run_variant_qa
from app.modules.social_media.services.media_assets import media_asset_service
from app.modules.social_media.services.performance import refresh_performance_insights
from app.modules.social_media.services.publishing import SocialPublishingService

logger = structlog.get_logger()


class SocialMediaService:
    """Coordinates the social workflow without embedding provider SDK logic."""

    DEFAULT_ORGANIZATION_SLUG = "winsta"

    def __init__(
        self,
        organization_repo: SocialOrganizationRepository,
        connection_repo: SocialConnectionRepository,
        brief_repo: SocialBriefRepository,
        content_repo: SocialContentRepository,
        publish_job_repo: SocialPublishJobRepository,
        campaign_repo: SocialCampaignRepository | None = None,
        organization_id: uuid.UUID | None = None,
    ) -> None:
        self.organization_repo = organization_repo
        self.connection_repo = connection_repo
        self.brief_repo = brief_repo
        self.content_repo = content_repo
        self.publish_job_repo = publish_job_repo
        self.campaign_repo = campaign_repo
        self.organization_id = organization_id

        # Specialized Sub-Services
        self.campaigns = SocialCampaignService(campaign_repo, brief_repo)
        self.publishing = SocialPublishingService(content_repo, publish_job_repo)

    async def _get_default_organization(self):
        if self.organization_id is not None:
            organization = await self.organization_repo.get_by_id(self.organization_id)
            if organization and organization.status == "active":
                return organization
            raise NotFoundException(message="Active workspace not found")
        organization = await self.organization_repo.get_by_slug(self.DEFAULT_ORGANIZATION_SLUG)
        if organization:
            return organization
        return await self.organization_repo.create({
            "slug": self.DEFAULT_ORGANIZATION_SLUG,
            "name": "Winsta AI",
            "status": "active",
        })

    async def create_brief(
        self,
        data: CreateContentBriefRequest,
        created_by: uuid.UUID | None,
    ) -> SocialBriefQueuedResponse:
        organization = await self._get_default_organization()
        brief_data = dict(data.brief_data or {})
        if data.media_url:
            brief_data["media_url"] = str(data.media_url)
        brief_data.update({
            "generate_image": data.generate_image,
            "image_model": data.image_model,
        })
        if data.visual_prompt:
            brief_data["visual_prompt"] = data.visual_prompt
        brief = await self.brief_repo.create({
            "organization_id": organization.id,
            "source_trend_id": data.source_trend_id,
            "source_prompt_package_id": data.source_prompt_package_id,
            "created_by": created_by,
            "title": data.title,
            "objective": data.objective,
            "campaign_type": data.campaign_type,
            "target_platforms": [platform.value for platform in data.target_platforms],
            "target_audience": data.target_audience,
            "tone": data.tone,
            "language": data.language,
            "target_languages": data.languages,
            "brief_data": brief_data or None,
            "status": ContentBriefStatus.QUEUED.value,
        })

        try:
            from app.workers.social_tasks import generate_social_content
            generate_social_content.delay(str(brief.id))
        except Exception as exc:
            logger.warning("social_content_dispatch_failed", brief_id=str(brief.id), error=str(exc))

        return SocialBriefQueuedResponse(id=brief.id, status=brief.status)

    async def create_campaign(
        self,
        data: CreateCampaignRequest,
        created_by: uuid.UUID | None,
    ) -> SocialCampaignResponse:
        org = await self._get_default_organization()
        return await self.campaigns.create_campaign(org.id, data, created_by)

    async def list_campaigns(self, *, page: int = 1, page_size: int = 20, status: str | None = None) -> dict:
        org = await self._get_default_organization()
        return await self.campaigns.list_campaigns(org.id, page=page, page_size=page_size, status=status)

    async def get_campaign(self, campaign_id: uuid.UUID) -> SocialCampaignResponse:
        org = await self._get_default_organization()
        return await self.campaigns.get_campaign(org.id, campaign_id)

    async def transition_campaign(
        self,
        campaign_id: uuid.UUID,
        target_status: CampaignStatus,
        actor_id: uuid.UUID | None,
        notes: str | None = None,
    ) -> SocialCampaignResponse:
        org = await self._get_default_organization()
        return await self.campaigns.transition_campaign(org.id, campaign_id, target_status, actor_id, notes)

    async def _get_campaign(self, campaign_id: uuid.UUID) -> SocialCampaign:
        org = await self._get_default_organization()
        return await self.campaigns.get_campaign_model(org.id, campaign_id)

    async def get_brief(self, brief_id: uuid.UUID) -> ContentBriefResponse:
        organization = await self._get_default_organization()
        brief = await self.brief_repo.get_by_id(brief_id)
        if not brief or brief.organization_id != organization.id:
            raise NotFoundException(message="Social content brief not found")
        await self._refresh_variant_media_urls(brief.content_items)
        return ContentBriefResponse.model_validate(brief)

    async def list_briefs(self, page: int = 1, page_size: int = 20) -> dict:
        organization = await self._get_default_organization()
        result = await self.brief_repo.paginate(
            page=page,
            page_size=page_size,
            filters=[ContentBrief.organization_id == organization.id],
        )
        content_items = [item for brief in result["items"] for item in brief.content_items]
        await self._refresh_variant_media_urls(content_items)
        result["items"] = [ContentBriefResponse.model_validate(item) for item in result["items"]]
        return result

    async def list_content(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict:
        if status:
            try:
                ContentItemStatus(status)
            except ValueError as exc:
                raise BadRequestException(message=f"Unknown social content status '{status}'") from exc
        organization = await self._get_default_organization()
        result = await self.content_repo.paginate_queue(
            page=page,
            page_size=page_size,
            status=status,
            organization_id=organization.id,
        )
        await self._refresh_variant_media_urls(result["items"])
        result["items"] = [
            SocialContentQueueItemResponse(
                id=item.id,
                brief_id=item.brief_id,
                brief_title=item.brief.title,
                target_platforms=item.brief.target_platforms,
                concept=item.concept,
                status=item.status,
                ai_provider=item.ai_provider,
                ai_model=item.ai_model,
                content_data=item.content_data,
                variants=item.variants,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
            for item in result["items"]
        ]
        return result

    async def _refresh_variant_media_urls(self, content_items: list) -> None:
        if not media_asset_service.configured:
            return
        variants = [
            variant
            for item in content_items
            for variant in item.variants
            if variant.media_asset_id
        ]
        asset_ids = {variant.media_asset_id for variant in variants}
        if not asset_ids:
            return
        result = await self.content_repo.session.execute(
            select(SocialMediaAsset)
            .where(SocialMediaAsset.id.in_(asset_ids))
            .where(SocialMediaAsset.status == "ready")
            .where(SocialMediaAsset.deleted_at.is_(None))
        )
        assets = list(result.scalars().all())
        signed_urls = await asyncio.gather(
            *(media_asset_service.signed_url(asset) for asset in assets),
            return_exceptions=True,
        )
        url_by_id = {
            asset.id: signed_url
            for asset, signed_url in zip(assets, signed_urls)
            if isinstance(signed_url, str)
        }
        for variant in variants:
            if variant.media_asset_id in url_by_id:
                variant.media_ref = url_by_id[variant.media_asset_id]

    async def list_publish_jobs(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> dict:
        org = await self._get_default_organization()
        return await self.publishing.list_publish_jobs(org.id, page=page, page_size=page_size, status=status)

    async def list_analytics(self, limit: int = 100) -> list[SocialMetricSnapshotResponse]:
        organization = await self._get_default_organization()
        result = await self.content_repo.session.execute(
            select(SocialMetricSnapshot)
            .where(SocialMetricSnapshot.organization_id == organization.id)
            .where(SocialMetricSnapshot.deleted_at.is_(None))
            .order_by(SocialMetricSnapshot.captured_at.desc())
            .limit(limit)
        )
        return [SocialMetricSnapshotResponse.model_validate(item) for item in result.scalars().all()]

    async def _get_active_brand_kit(self, organization_id: uuid.UUID) -> BrandKit | None:
        return await SocialBrandKitService.get_active_brand_kit(self.content_repo.session, organization_id)

    @staticmethod
    def _brand_context(brand_kit: BrandKit | None) -> dict:
        return SocialBrandKitService.brand_context(brand_kit)

    async def get_brand_kit(self) -> BrandKitResponse:
        org = await self._get_default_organization()
        return await SocialBrandKitService.get_or_create_brand_kit(self.content_repo.session, org.id)

    async def update_brand_kit(self, data: UpdateBrandKitRequest) -> BrandKitResponse:
        org = await self._get_default_organization()
        return await SocialBrandKitService.update_brand_kit(self.content_repo.session, org.id, data)

    async def list_performance_insights(self) -> list[SocialPerformanceInsightResponse]:
        organization = await self._get_default_organization()
        result = await self.content_repo.session.execute(
            select(SocialPerformanceInsight)
            .where(SocialPerformanceInsight.organization_id == organization.id)
            .where(SocialPerformanceInsight.status == "active")
            .where(SocialPerformanceInsight.deleted_at.is_(None))
            .order_by(
                SocialPerformanceInsight.platform.asc().nullsfirst(),
                SocialPerformanceInsight.performance_score.desc(),
            )
        )
        return [
            SocialPerformanceInsightResponse.model_validate(item)
            for item in result.scalars().all()
        ]

    async def analyze_performance(self) -> list[SocialPerformanceInsightResponse]:
        organization = await self._get_default_organization()
        insights = await refresh_performance_insights(
            self.content_repo.session,
            organization.id,
        )
        await self.content_repo.session.commit()
        return [SocialPerformanceInsightResponse.model_validate(item) for item in insights]

    async def upload_media_asset(
        self,
        *,
        content: bytes,
        mime_type: str,
        source_name: str | None = None,
    ) -> SocialMediaAssetResponse:
        organization = await self._get_default_organization()
        stored = await media_asset_service.store_bytes(
            self.content_repo.session,
            organization_id=organization.id,
            content=content,
            mime_type=mime_type,
            provider="manual_upload",
            metadata={"source_name": source_name} if source_name else {},
        )
        await self.content_repo.session.commit()
        return self._asset_response(stored.asset, stored.signed_url)

    async def list_media_assets(self, limit: int = 100) -> list[SocialMediaAssetResponse]:
        organization = await self._get_default_organization()
        result = await self.content_repo.session.execute(
            select(SocialMediaAsset)
            .where(SocialMediaAsset.organization_id == organization.id)
            .where(SocialMediaAsset.deleted_at.is_(None))
            .order_by(SocialMediaAsset.created_at.desc())
            .limit(limit)
        )
        responses: list[SocialMediaAssetResponse] = []
        for asset in result.scalars().all():
            signed_url = await media_asset_service.signed_url(asset) if media_asset_service.configured else None
            responses.append(self._asset_response(asset, signed_url))
        return responses

    async def get_media_asset_url(self, asset_id: uuid.UUID) -> SocialMediaAssetResponse:
        organization = await self._get_default_organization()
        result = await self.content_repo.session.execute(
            select(SocialMediaAsset)
            .where(SocialMediaAsset.id == asset_id)
            .where(SocialMediaAsset.organization_id == organization.id)
            .where(SocialMediaAsset.deleted_at.is_(None))
        )
        asset = result.scalar_one_or_none()
        if not asset:
            raise NotFoundException(message="Social media asset not found")
        return self._asset_response(asset, await media_asset_service.signed_url(asset))

    @staticmethod
    def _asset_response(asset: SocialMediaAsset, signed_url: str | None) -> SocialMediaAssetResponse:
        return SocialMediaAssetResponse(
            id=asset.id,
            organization_id=asset.organization_id,
            content_item_id=asset.content_item_id,
            storage_bucket=asset.storage_bucket,
            storage_path=asset.storage_path,
            source_url=asset.source_url,
            signed_url=signed_url,
            mime_type=asset.mime_type,
            media_type=asset.media_type,
            size_bytes=asset.size_bytes,
            sha256=asset.sha256,
            provider=asset.provider,
            prompt=asset.prompt,
            aspect_ratio=asset.aspect_ratio,
            status=asset.status,
            metadata=asset.metadata_ or {},
            created_at=asset.created_at,
            updated_at=asset.updated_at,
        )

    async def list_connection_catalog(self) -> list[SocialPlatformConnectionResponse]:
        organization = await self._get_default_organization()
        connections = await self.connection_repo.list_for_organization(organization.id)
        settings = get_settings()
        catalog: list[SocialPlatformConnectionResponse] = []
        for spec in PROVIDER_SPECS:
            accounts = [connection for connection in connections if connection.platform == spec.platform]
            connected = any(account.status == "connected" for account in accounts)
            missing_settings = missing_provider_settings(settings, spec)
            if connected:
                connection_status = "connected"
            elif missing_settings:
                connection_status = "configuration_required"
            else:
                connection_status = "ready_to_authorize"
            catalog.append(
                SocialPlatformConnectionResponse(
                    platform=spec.platform,
                    display_name=spec.display_name,
                    description=spec.description,
                    setup_url=spec.setup_url,
                    callback_url=callback_url(settings, spec.platform),
                    requested_scopes=list(requested_scopes(settings, spec)),
                    status=connection_status,
                    missing_settings=missing_settings,
                    accounts=[SocialConnectionAccountResponse.model_validate(account) for account in accounts],
                )
            )
        return catalog

    def get_oauth_diagnostics(self) -> SocialOAuthDiagnosticsResponse:
        return SocialOAuthDiagnosticsResponse.model_validate(oauth_diagnostics(get_settings()))

    async def begin_connection(self, platform: str, created_by: uuid.UUID | None = None) -> BeginSocialConnectionResponse:
        spec = get_provider_spec(platform)
        if spec is None:
            raise BadRequestException(message=f"Unsupported social platform '{platform}'")
        settings = get_settings()
        missing_settings = missing_provider_settings(settings, spec)
        provider_callback_url = callback_url(settings, platform)
        if missing_settings:
            return BeginSocialConnectionResponse(
                platform=platform,
                status="configuration_required",
                message="Configure the provider application on the backend before starting OAuth.",
                callback_url=provider_callback_url,
                missing_settings=missing_settings,
            )
        state = secrets.token_urlsafe(32)
        provider = "meta" if platform == "facebook" else platform
        oauth_metadata: dict[str, str] = {}
        authorization_kwargs: dict[str, str] = {}
        if platform == "x":
            verifier, challenge = create_pkce_pair()
            oauth_metadata["code_verifier"] = verifier
            authorization_kwargs["code_challenge"] = challenge
        self.content_repo.session.add(SocialOAuthState(
            organization_id=(await self._get_default_organization()).id,
            created_by=created_by,
            provider=provider,
            platform=platform,
            state_hash=hash_state(state),
            redirect_uri=provider_callback_url,
            metadata_=oauth_metadata or None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        ))
        await self.content_repo.session.flush()
        spec = next(spec for spec in PROVIDER_SPECS if spec.platform == platform)
        scopes = requested_scopes(settings, spec)
        if provider == "meta":
            authorization_url = MetaGraphClient().authorization_url(
                state=state, redirect_uri=provider_callback_url, scopes=list(scopes)
            )
        else:
            authorization_url = get_oauth_client(platform).authorization_url(
                state=state,
                redirect_uri=provider_callback_url,
                scopes=list(scopes),
                **authorization_kwargs,
            )
        return BeginSocialConnectionResponse(
            platform=platform,
            status="ready_to_authorize",
            message=f"{spec.display_name} OAuth is ready. Continue in the provider authorization window.",
            callback_url=provider_callback_url,
            authorization_url=authorization_url,
        )

    async def complete_connection(self, *, state: str, code: str | None, error: str | None) -> str:
        state_result = await self.content_repo.session.execute(
            select(SocialOAuthState)
            .where(SocialOAuthState.state_hash == hash_state(state))
            .where(SocialOAuthState.consumed_at.is_(None))
            .where(SocialOAuthState.expires_at > datetime.now(timezone.utc))
            .where(SocialOAuthState.deleted_at.is_(None))
        )
        oauth_state = state_result.scalar_one_or_none()
        if not oauth_state:
            raise OAuthConnectionError(
                reason="invalid_state",
                message="OAuth state is invalid, expired, or already used",
            )
        oauth_state.consumed_at = datetime.now(timezone.utc)
        if error or not code:
            await self.content_repo.session.commit()
            raise OAuthConnectionError(
                reason="provider_denied",
                platform=oauth_state.platform,
                message="The provider authorization was cancelled or denied",
            )
        try:
            if oauth_state.provider == "meta":
                await self._complete_meta_connection(oauth_state=oauth_state, code=code)
            else:
                await self._complete_standard_connection(oauth_state=oauth_state, code=code)
        except BadRequestException as exc:
            platform = oauth_state.platform
            await self.content_repo.session.rollback()
            message = exc.message.lower()
            if "permission" in message:
                reason = "missing_permissions"
            elif "manageable" in message:
                reason = "no_manageable_account"
            else:
                reason = "provider_response_invalid"
            raise OAuthConnectionError(
                reason=reason,
                platform=platform,
                message=(
                    "Meta did not grant every permission required for this connection"
                    if reason == "missing_permissions"
                    else "The provider did not return a publishable account"
                ),
            ) from exc
        except ExternalServiceException as exc:
            platform = oauth_state.platform
            await self.content_repo.session.rollback()
            error_text = str(getattr(exc, "message", exc)).lower()
            if platform == "tiktok" and "scope_not_authorized" in error_text:
                raise OAuthConnectionError(
                    reason="scope_not_authorized",
                    platform=platform,
                    message=(
                        "TikTok did not authorize the requested scope. "
                        "Enable it for this Sandbox app and target user, then reconnect."
                    ),
                ) from exc
            raise OAuthConnectionError(
                reason="provider_exchange_failed",
                platform=platform,
                message="The provider rejected the token or account exchange",
            ) from exc
        except Exception as exc:
            platform = oauth_state.platform
            await self.content_repo.session.rollback()
            raise OAuthConnectionError(
                reason="connection_failed",
                platform=platform,
                message="The social account connection could not be completed",
            ) from exc
        await self.content_repo.session.commit()
        return "connected"

    async def _complete_standard_connection(self, *, oauth_state: SocialOAuthState, code: str) -> None:
        spec = get_provider_spec(oauth_state.platform)
        if not spec:
            raise BadRequestException(message="OAuth platform is no longer supported")
        active_scopes = requested_scopes(get_settings(), spec)
        client = get_oauth_client(oauth_state.platform)
        token = await client.exchange_code(
            code=code,
            redirect_uri=oauth_state.redirect_uri,
            scopes=list(active_scopes),
            **(oauth_state.metadata_ or {}),
        )
        account = await client.get_account(token.access_token)
        credential = SocialCredential(
            organization_id=oauth_state.organization_id,
            provider=oauth_state.provider,
            credential_type="oauth2",
            encrypted_access_token=encrypt_secret(token.access_token),
            encrypted_refresh_token=(encrypt_secret(token.refresh_token) if token.refresh_token else None),
            expires_at=token.expires_at,
            scopes=token.scopes,
            metadata_={"token_type": token.raw.get("token_type", "Bearer")},
        )
        self.content_repo.session.add(credential)
        await self.content_repo.session.flush()
        await self._upsert_connection(
            organization_id=oauth_state.organization_id,
            platform=oauth_state.platform,
            account_id=account.account_id,
            account_name=account.account_name,
            credential_ref=str(credential.id),
            scopes=token.scopes,
            metadata_=account.metadata,
        )

    async def _complete_meta_connection(self, *, oauth_state: SocialOAuthState, code: str) -> None:
        client = MetaGraphClient()
        token_payload = await client.exchange_code(code=code, redirect_uri=oauth_state.redirect_uri)
        spec = get_provider_spec(oauth_state.platform)
        if not spec:
            raise BadRequestException(message="Meta OAuth platform is no longer supported")
        granted_scopes = await client.list_granted_permissions(token_payload["access_token"])
        missing_scopes = sorted(set(spec.requested_scopes) - set(granted_scopes))
        if missing_scopes:
            raise BadRequestException(
                message=f"Meta did not grant required permissions: {', '.join(missing_scopes)}"
            )
        pages = await client.list_pages(token_payload["access_token"])
        if not pages:
            raise BadRequestException(message="No manageable Facebook Page was returned by Meta")
        for page in pages:
            page_token, page_id = page.get("access_token"), page.get("id")
            if not page_token or not page_id:
                continue
            credential = SocialCredential(
                organization_id=oauth_state.organization_id,
                provider="meta",
                credential_type="oauth2",
                encrypted_access_token=encrypt_secret(page_token),
                expires_at=token_payload.get("expires_at"),
                scopes=granted_scopes,
                metadata_={"page_id": page_id},
            )
            self.content_repo.session.add(credential)
            await self.content_repo.session.flush()
            await self._upsert_connection(
                organization_id=oauth_state.organization_id,
                platform="facebook",
                account_id=page_id,
                account_name=page.get("name"),
                credential_ref=str(credential.id),
                scopes=credential.scopes,
                metadata_={"page_id": page_id},
            )
            instagram_account = page.get("instagram_business_account") or {}
            if instagram_account.get("id"):
                await self._upsert_connection(
                    organization_id=oauth_state.organization_id,
                    platform="instagram",
                    account_id=instagram_account["id"],
                    account_name=f"{page.get('name', 'Facebook Page')} Instagram",
                    credential_ref=str(credential.id),
                    scopes=granted_scopes,
                    metadata_={"facebook_page_id": page_id},
                )

    async def _upsert_connection(self, **data) -> None:
        result = await self.content_repo.session.execute(
            select(SocialConnection).where(
                SocialConnection.organization_id == data["organization_id"],
                SocialConnection.platform == data["platform"],
                SocialConnection.account_id == data["account_id"],
                SocialConnection.deleted_at.is_(None),
            )
        )
        connection = result.scalar_one_or_none()
        if connection:
            for key, value in data.items():
                if key != "organization_id":
                    setattr(connection, key, value)
            connection.status = "connected"
        else:
            self.content_repo.session.add(SocialConnection(**data, status="connected"))
        await self.content_repo.session.flush()

    async def review_content(
        self,
        content_id: uuid.UUID,
        data: ApproveContentRequest,
        reviewer_id: uuid.UUID | None,
    ) -> ContentItemResponse:
        organization = await self._get_default_organization()
        item = await self.content_repo.get_by_id(content_id)
        if not item or item.organization_id != organization.id:
            raise NotFoundException(message="Social content item not found")

        current_status = ContentItemStatus(item.status)
        if not current_status.is_approvable:
            raise BadRequestException(
                message=f"Content in '{item.status}' status cannot be reviewed. Must be 'ready_for_approval'."
            )

        variants = list(item.variants)
        all_variant_ids = {variant.id for variant in variants}
        if data.variant_ids:
            selected_ids = set(data.variant_ids)
            if selected_ids - all_variant_ids:
                raise BadRequestException(message="One or more variants do not belong to this content item")
            variants = [variant for variant in variants if variant.id in selected_ids]
        decision_status = (
            ContentItemStatus.APPROVED.value
            if data.decision.value == "approve"
            else ContentItemStatus.REJECTED.value
        )
        for variant in variants:
            variant.status = decision_status
        variant_statuses = {variant.status for variant in item.variants}
        if variant_statuses == {ContentItemStatus.APPROVED.value}:
            item.status = ContentItemStatus.APPROVED.value
            item.brief.status = ContentBriefStatus.COMPLETED.value
        elif variant_statuses == {ContentItemStatus.REJECTED.value}:
            item.status = ContentItemStatus.REJECTED.value
            item.brief.status = ContentBriefStatus.COMPLETED.value
        else:
            item.status = ContentItemStatus.READY_FOR_APPROVAL.value
            item.brief.status = ContentBriefStatus.READY_FOR_REVIEW.value
        self.content_repo.session.add(ContentApproval(
            organization_id=item.organization_id,
            content_item_id=item.id,
            reviewer_id=reviewer_id,
            decision=data.decision.value,
            notes=data.notes,
            variant_ids=[str(variant.id) for variant in variants],
        ))
        await self.content_repo.session.flush()
        await self.content_repo.session.refresh(item)
        return ContentItemResponse.model_validate(item)

    async def update_variant(
        self,
        variant_id: uuid.UUID,
        data: UpdateContentVariantRequest,
    ) -> ContentItemResponse:
        organization = await self._get_default_organization()
        variant = await self.content_repo.session.get(ContentVariant, variant_id)
        if not variant or variant.deleted_at is not None:
            raise NotFoundException(message="Social content variant not found")
        item = await self.content_repo.get_by_id(variant.content_item_id)
        if not item or item.organization_id != organization.id:
            raise NotFoundException(message="Social content item not found")
        active_jobs = await self.publish_job_repo.get_all(
            filters=[
                PublishJob.content_variant_id == variant.id,
                PublishJob.status.in_([
                    PublishJobStatus.QUEUED.value,
                    PublishJobStatus.SCHEDULED.value,
                    PublishJobStatus.PUBLISHING.value,
                ]),
            ],
            limit=1,
        )
        if active_jobs:
            raise ConflictException(message="Cancel the active publish job before editing this variant")

        changes = data.model_dump(exclude_unset=True)
        if "media_ref" in changes and changes["media_ref"] is not None:
            source_url = str(changes["media_ref"])
            if media_asset_service.configured:
                stored = await media_asset_service.store_remote(
                    self.content_repo.session,
                    organization_id=item.organization_id,
                    content_item_id=item.id,
                    source_url=source_url,
                    provider="variant_edit",
                    prompt=variant.visual_prompt,
                    aspect_ratio=variant.aspect_ratio,
                    metadata={"variant_id": str(variant.id)},
                )
                changes["media_ref"] = stored.signed_url
                variant.media_asset_id = stored.asset.id
            else:
                changes["media_ref"] = source_url
        elif "media_ref" in changes:
            variant.media_asset_id = None
        for field, value in changes.items():
            setattr(variant, field, value)
        variant.version += 1
        brand_kit = await self._get_active_brand_kit(item.organization_id)
        qa_result = run_variant_qa({
            "platform": variant.platform,
            "language": variant.language,
            "caption": variant.caption,
            "hook": variant.hook,
            "cta": variant.cta,
            "hashtags": variant.hashtags,
            "media_ref": variant.media_ref,
        }, self._brand_context(brand_kit))
        variant.qa_status = qa_result["status"]
        variant.qa_result = qa_result
        variant.status = (
            ContentItemStatus.READY_FOR_APPROVAL.value
            if qa_result["status"] == "passed"
            else ContentItemStatus.FAILED.value
        )
        item.status = variant.status
        item.brief.status = (
            ContentBriefStatus.READY_FOR_REVIEW.value
            if qa_result["status"] == "passed"
            else ContentBriefStatus.FAILED.value
        )
        await self.content_repo.session.flush()
        return ContentItemResponse.model_validate(item)

    async def schedule_content(
        self,
        content_id: uuid.UUID,
        data: ScheduleContentRequest,
    ) -> list[PublishJobResponse]:
        org = await self._get_default_organization()
        return await self.publishing.schedule_content(org.id, content_id, data)

    async def cancel_publish_job(self, job_id: uuid.UUID) -> PublishJobResponse:
        org = await self._get_default_organization()
        return await self.publishing.cancel_publish_job(org.id, job_id)

    async def retry_publish_job(self, job_id: uuid.UUID) -> PublishJobResponse:
        org = await self._get_default_organization()
        return await self.publishing.retry_publish_job(org.id, job_id)

    async def reschedule_publish_job(
        self,
        job_id: uuid.UUID,
        data: ReschedulePublishJobRequest,
    ) -> PublishJobResponse:
        org = await self._get_default_organization()
        return await self.publishing.reschedule_publish_job(org.id, job_id, data)
