"""Sub-service managing Social Campaigns lifecycle and operations."""

from datetime import datetime, timezone
from typing import Any
import uuid

from app.core.exceptions import BadRequestException, ExternalServiceException, NotFoundException
from app.modules.social_media.enums import CampaignStatus
from app.modules.social_media.models import SocialCampaign
from app.modules.social_media.repositories import SocialBriefRepository, SocialCampaignRepository
from app.modules.social_media.schemas import CreateCampaignRequest, SocialCampaignResponse


class SocialCampaignService:
    """Encapsulates campaign lifecycle state transitions and CRUD."""

    def __init__(
        self,
        campaign_repo: SocialCampaignRepository | None,
        brief_repo: SocialBriefRepository,
    ) -> None:
        self.campaign_repo = campaign_repo
        self.brief_repo = brief_repo

    def _ensure_repo(self) -> SocialCampaignRepository:
        if self.campaign_repo is None:
            raise ExternalServiceException(message="Campaign service is not configured")
        return self.campaign_repo

    async def get_campaign_model(self, organization_id: uuid.UUID, campaign_id: uuid.UUID) -> SocialCampaign:
        repo = self._ensure_repo()
        campaign = await repo.get_by_id(campaign_id)
        if not campaign or campaign.organization_id != organization_id:
            raise NotFoundException(message="Campaign not found")
        return campaign

    async def get_campaign(self, organization_id: uuid.UUID, campaign_id: uuid.UUID) -> SocialCampaignResponse:
        campaign = await self.get_campaign_model(organization_id, campaign_id)
        return SocialCampaignResponse.model_validate(campaign)

    async def create_campaign(
        self,
        organization_id: uuid.UUID,
        data: CreateCampaignRequest,
        created_by: uuid.UUID | None,
    ) -> SocialCampaignResponse:
        repo = self._ensure_repo()
        if data.brief_id:
            brief = await self.brief_repo.get_by_id(data.brief_id)
            if not brief or brief.organization_id != organization_id:
                raise NotFoundException(message="Linked social content brief not found")
        campaign = await repo.create({
            "organization_id": organization_id,
            "created_by": created_by,
            "name": data.name,
            "objective": data.objective,
            "platforms": [platform.value for platform in data.platforms],
            "budget_cents": data.budget_cents,
            "budget_type": data.budget_type.value,
            "currency": data.currency,
            "start_at": data.start_at,
            "end_at": data.end_at,
            "audience": data.audience,
            "creative_variant_ids": [str(value) for value in data.creative_variant_ids],
            "brief_id": data.brief_id,
            "notes": data.notes,
            "status": CampaignStatus.DRAFT.value,
        })
        return SocialCampaignResponse.model_validate(campaign)

    async def list_campaigns(
        self,
        organization_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict:
        repo = self._ensure_repo()
        if status:
            try:
                CampaignStatus(status)
            except ValueError as exc:
                raise BadRequestException(message=f"Unknown campaign status '{status}'") from exc
        result = await repo.paginate_for_organization(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            status=status,
        )
        result["items"] = [SocialCampaignResponse.model_validate(item) for item in result["items"]]
        return result

    async def transition_campaign(
        self,
        organization_id: uuid.UUID,
        campaign_id: uuid.UUID,
        target_status: CampaignStatus,
        actor_id: uuid.UUID | None,
        notes: str | None = None,
    ) -> SocialCampaignResponse:
        repo = self._ensure_repo()
        campaign = await self.get_campaign_model(organization_id, campaign_id)
        allowed = {
            CampaignStatus.DRAFT: {CampaignStatus.PENDING_APPROVAL},
            CampaignStatus.REJECTED: {CampaignStatus.PENDING_APPROVAL},
            CampaignStatus.PENDING_APPROVAL: {CampaignStatus.APPROVED, CampaignStatus.REJECTED},
            CampaignStatus.APPROVED: {CampaignStatus.ACTIVE, CampaignStatus.COMPLETED},
            CampaignStatus.ACTIVE: {CampaignStatus.PAUSED, CampaignStatus.COMPLETED},
            CampaignStatus.PAUSED: {CampaignStatus.ACTIVE, CampaignStatus.COMPLETED},
            CampaignStatus.COMPLETED: set(),
        }
        current_status = CampaignStatus(campaign.status)
        if target_status not in allowed[current_status]:
            raise BadRequestException(
                message=f"Cannot transition campaign from '{campaign.status}' to '{target_status.value}'"
            )
        values: dict[str, Any] = {"status": target_status.value}
        if notes is not None:
            values["notes"] = notes
        if target_status is CampaignStatus.APPROVED:
            values["approved_by"] = actor_id
            values["approved_at"] = datetime.now(timezone.utc)
        if target_status is CampaignStatus.PENDING_APPROVAL:
            values["approved_by"] = None
            values["approved_at"] = None
        updated = await repo.update(campaign.id, values)
        if updated is None:
            raise NotFoundException(message="Campaign not found")
        return SocialCampaignResponse.model_validate(updated)

