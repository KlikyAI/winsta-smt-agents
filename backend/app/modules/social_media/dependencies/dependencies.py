from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_organization_id
from app.modules.social_media.repositories import (
    SocialCampaignRepository,
    SocialBriefRepository,
    SocialConnectionRepository,
    SocialContentRepository,
    SocialOrganizationRepository,
    SocialPublishJobRepository,
)
from app.modules.social_media.services import SocialMediaService


async def get_social_media_service(
    db: AsyncSession = Depends(get_db),
    organization_id = Depends(get_current_organization_id),
) -> SocialMediaService:
    return SocialMediaService(
        organization_repo=SocialOrganizationRepository(db),
        connection_repo=SocialConnectionRepository(db),
        brief_repo=SocialBriefRepository(db),
        content_repo=SocialContentRepository(db),
        publish_job_repo=SocialPublishJobRepository(db),
        organization_id=organization_id,
        campaign_repo=SocialCampaignRepository(db),
    )
