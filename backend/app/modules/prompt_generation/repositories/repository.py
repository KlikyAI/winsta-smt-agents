"""Prompt Generation module — repository."""

import uuid
from datetime import datetime
from typing import Literal, Optional, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.modules.prompt_generation.models import PromptPackage
from app.shared.base_repository import BaseRepository


class PromptPackageRepository(BaseRepository[PromptPackage]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(PromptPackage, session)

    async def get_by_trend(self, trend_id: uuid.UUID) -> Sequence[PromptPackage]:
        stmt = (
            select(PromptPackage)
            .where(PromptPackage.trend_id == trend_id)
            .where(PromptPackage.deleted_at.is_(None))
            .order_by(PromptPackage.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(self, trend_id: uuid.UUID) -> Optional[PromptPackage]:
        stmt = (
            select(PromptPackage)
            .where(PromptPackage.trend_id == trend_id)
            .where(PromptPackage.deleted_at.is_(None))
            .order_by(PromptPackage.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_version(self, trend_id: uuid.UUID) -> int:
        latest = await self.get_latest(trend_id)
        return (latest.version + 1) if latest else 1

    async def list_public(
        self,
        *,
        page: int,
        page_size: int,
        date_from: datetime | None = None,
        date_to_exclusive: datetime | None = None,
        category: str | None = None,
        search: str | None = None,
        has_reference_image: bool | None = None,
        min_quality_score: float | None = None,
        generation_mode: str | None = None,
        latest_only: bool = True,
        sort: Literal["newest", "oldest", "quality_desc"] = "newest",
    ) -> tuple[Sequence[PromptPackage], int]:
        """List only validated prompt packages through the public contract."""
        conditions = [
            PromptPackage.deleted_at.is_(None),
            PromptPackage.validation_status == "passed",
        ]
        if date_from:
            conditions.append(PromptPackage.created_at >= date_from)
        if date_to_exclusive:
            conditions.append(PromptPackage.created_at < date_to_exclusive)
        if category:
            conditions.append(func.lower(PromptPackage.category) == category.strip().lower())
        if search:
            pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    PromptPackage.trend_title.ilike(pattern),
                    PromptPackage.description.ilike(pattern),
                    PromptPackage.core_concept.ilike(pattern),
                )
            )
        if has_reference_image is True:
            conditions.append(PromptPackage.trend_reference_image_url.is_not(None))
        elif has_reference_image is False:
            conditions.append(PromptPackage.trend_reference_image_url.is_(None))
        if min_quality_score is not None:
            conditions.append(PromptPackage.quality_score >= min_quality_score)
        if generation_mode:
            conditions.append(PromptPackage.generation_modes.contains([generation_mode.strip()]))
        if latest_only:
            latest = aliased(PromptPackage)
            latest_version = (
                select(func.max(latest.version))
                .where(
                    latest.trend_id == PromptPackage.trend_id,
                    latest.validation_status == "passed",
                    latest.deleted_at.is_(None),
                )
                .correlate(PromptPackage)
                .scalar_subquery()
            )
            conditions.append(PromptPackage.version == latest_version)

        total = (
            await self.session.execute(
                select(func.count()).select_from(PromptPackage).where(*conditions)
            )
        ).scalar_one()

        if sort == "oldest":
            ordering = (PromptPackage.created_at.asc(), PromptPackage.id.asc())
        elif sort == "quality_desc":
            ordering = (
                PromptPackage.quality_score.desc().nullslast(),
                PromptPackage.created_at.desc(),
                PromptPackage.id.desc(),
            )
        else:
            ordering = (PromptPackage.created_at.desc(), PromptPackage.id.desc())

        stmt = (
            select(PromptPackage)
            .where(*conditions)
            .order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total
