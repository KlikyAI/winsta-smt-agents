"""Trend Sources module — repository."""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.trend_sources.models import TrendSource
from app.shared.base_repository import BaseRepository


class TrendSourceRepository(BaseRepository[TrendSource]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendSource, session)

    async def get_by_platform(self, platform: str) -> Optional[TrendSource]:
        stmt = (
            select(TrendSource)
            .where(TrendSource.platform == platform)
            .where(TrendSource.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_enabled_sources(self) -> Sequence[TrendSource]:
        stmt = (
            select(TrendSource)
            .where(TrendSource.enabled.is_(True))
            .where(TrendSource.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
