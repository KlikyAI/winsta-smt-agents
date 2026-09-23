"""Database repositories for Social Media Agent workflows."""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import noload, selectinload

from app.modules.social_media.models import (
    ContentBrief,
    ContentItem,
    ContentVariant,
    PublishJob,
    SocialCampaign,
    SocialConnection,
    SocialOrganization,
)
from app.shared.base_repository import BaseRepository


class SocialOrganizationRepository(BaseRepository[SocialOrganization]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SocialOrganization, session)

    async def get_by_slug(self, slug: str) -> Optional[SocialOrganization]:
        result = await self.session.execute(
            select(SocialOrganization)
            .options(noload("*"))
            .where(SocialOrganization.slug == slug)
            .where(SocialOrganization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class SocialCampaignRepository(BaseRepository[SocialCampaign]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SocialCampaign, session)

    async def paginate_for_organization(
        self,
        *,
        organization_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict:
        filters = [SocialCampaign.organization_id == organization_id]
        if status:
            filters.append(SocialCampaign.status == status)
        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=SocialCampaign.created_at.desc(),
        )


class SocialConnectionRepository(BaseRepository[SocialConnection]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SocialConnection, session)

    async def list_for_organization(self, organization_id: uuid.UUID) -> list[SocialConnection]:
        result = await self.session.execute(
            select(SocialConnection)
            .where(SocialConnection.organization_id == organization_id)
            .where(SocialConnection.deleted_at.is_(None))
            .order_by(SocialConnection.platform, SocialConnection.account_name)
        )
        return list(result.scalars().all())


class SocialBriefRepository(BaseRepository[ContentBrief]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ContentBrief, session)

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[ContentBrief]:
        result = await self.session.execute(
            select(ContentBrief)
            .options(
                selectinload(ContentBrief.content_items).selectinload(ContentItem.variants),
            )
            .where(ContentBrief.id == record_id)
            .where(ContentBrief.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class SocialContentRepository(BaseRepository[ContentItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ContentItem, session)

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[ContentItem]:
        result = await self.session.execute(
            select(ContentItem)
            .options(selectinload(ContentItem.brief), selectinload(ContentItem.variants))
            .where(ContentItem.id == record_id)
            .where(ContentItem.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def paginate_queue(
        self,
        *,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        organization_id: uuid.UUID | None = None,
    ) -> dict:
        filters = [ContentItem.deleted_at.is_(None)]
        if organization_id is not None:
            filters.append(ContentItem.organization_id == organization_id)
        if status:
            filters.append(ContentItem.status == status)

        count_stmt = select(func.count()).select_from(ContentItem).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()
        stmt = (
            select(ContentItem)
            .options(selectinload(ContentItem.brief), selectinload(ContentItem.variants))
            .where(*filters)
            .order_by(ContentItem.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


class SocialPublishJobRepository(BaseRepository[PublishJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PublishJob, session)

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[PublishJob]:
        result = await self.session.execute(
            select(PublishJob)
            .options(
                selectinload(PublishJob.content_variant)
                .selectinload(ContentVariant.content_item)
                .selectinload(ContentItem.brief)
            )
            .where(PublishJob.id == record_id)
            .where(PublishJob.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def paginate_queue(
        self,
        *,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        organization_id: uuid.UUID | None = None,
    ) -> dict:
        filters = [PublishJob.deleted_at.is_(None)]
        if organization_id is not None:
            filters.append(PublishJob.organization_id == organization_id)
        if status:
            filters.append(PublishJob.status == status)

        count_stmt = select(func.count()).select_from(PublishJob).where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()
        stmt = (
            select(PublishJob)
            .options(
                selectinload(PublishJob.content_variant)
                .selectinload(ContentVariant.content_item)
                .selectinload(ContentItem.brief)
            )
            .where(*filters)
            .order_by(PublishJob.scheduled_at.asc().nullsfirst(), PublishJob.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = (await self.session.execute(stmt)).scalars().all()
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
