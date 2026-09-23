"""Trends module — FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.trends.repositories import TrendRepository
from app.modules.trends.services import TrendService


async def get_trend_repository(db: AsyncSession = Depends(get_db)) -> TrendRepository:
    return TrendRepository(db)


async def get_trend_service(
    repo: TrendRepository = Depends(get_trend_repository),
) -> TrendService:
    return TrendService(repo)
