"""Trend Runs module — repository."""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.trend_runs.models import TrendRun
from app.shared.base_repository import BaseRepository


class TrendRunRepository(BaseRepository[TrendRun]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendRun, session)

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[TrendRun]:
        """Get a single TrendRun by ID with pre-loaded candidates."""
        stmt = (
            select(TrendRun)
            .options(selectinload(TrendRun.candidates))
            .where(TrendRun.id == record_id)
            .where(TrendRun.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
