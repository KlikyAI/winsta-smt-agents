"""Trend Sources module — FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.trend_sources.repositories import TrendSourceRepository
from app.modules.trend_sources.services import TrendSourceService


async def get_trend_source_repository(db: AsyncSession = Depends(get_db)) -> TrendSourceRepository:
    return TrendSourceRepository(db)


async def get_trend_source_service(
    repo: TrendSourceRepository = Depends(get_trend_source_repository),
) -> TrendSourceService:
    return TrendSourceService(repo)
