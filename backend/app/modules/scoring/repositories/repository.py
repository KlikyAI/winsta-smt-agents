"""Scoring module — repository."""

from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scoring.models import ScoringConfiguration, TrendSignal
from app.shared.base_repository import BaseRepository


class ScoringConfigurationRepository(BaseRepository[ScoringConfiguration]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ScoringConfiguration, session)

    async def get_active_config(self) -> Sequence[ScoringConfiguration]:
        stmt = (
            select(ScoringConfiguration)
            .where(ScoringConfiguration.is_active.is_(True))
            .where(ScoringConfiguration.deleted_at.is_(None))
            .order_by(ScoringConfiguration.signal_type)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_current_version(self) -> int:
        stmt = (
            select(ScoringConfiguration.version)
            .where(ScoringConfiguration.deleted_at.is_(None))
            .order_by(ScoringConfiguration.version.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        version = result.scalar_one_or_none()
        return version or 0

    async def deactivate_all(self) -> None:
        active = await self.get_active_config()
        for config in active:
            config.is_active = False
        await self.session.flush()


class TrendSignalRepository(BaseRepository[TrendSignal]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendSignal, session)
