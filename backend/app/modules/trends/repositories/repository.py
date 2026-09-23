"""Trends module — repository."""

import uuid
from typing import Any, Optional, Sequence

from sqlalchemy import Float, select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.trends.models import Trend, TrendEvidence
from app.shared.base_repository import BaseRepository


class TrendRepository(BaseRepository[Trend]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Trend, session)

    async def get_detail(self, trend_id: uuid.UUID) -> Optional[Trend]:
        """Get a trend with all relationships loaded."""
        stmt = (
            select(Trend)
            .options(
                selectinload(Trend.evidence),
                selectinload(Trend.signals),
                selectinload(Trend.prompt_packages),
                selectinload(Trend.reviews),
            )
            .where(Trend.id == trend_id)
            .where(Trend.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def query_trends(
        self,
        *,
        status: Optional[str] = None,
        category: Optional[str] = None,
        minimum_score: Optional[float] = None,
        language: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Query trends with filtering and pagination."""
        filters: list[Any] = []

        if status:
            filters.append(Trend.status == status)
        if category:
            filters.append(Trend.category == category)
        if minimum_score is not None:
            filters.append(Trend.overall_score >= minimum_score)
        if search:
            search_filter = or_(
                Trend.title.ilike(f"%{search}%"),
                Trend.description.ilike(f"%{search}%"),
                Trend.core_concept.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        return await self.paginate(
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=Trend.created_at.desc(),
        )


class TrendEvidenceRepository(BaseRepository[TrendEvidence]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendEvidence, session)

    async def get_by_trend(self, trend_id: uuid.UUID) -> Sequence[TrendEvidence]:
        stmt = (
            select(TrendEvidence)
            .where(TrendEvidence.trend_id == trend_id)
            .where(TrendEvidence.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
