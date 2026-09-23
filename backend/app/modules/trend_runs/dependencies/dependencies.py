"""Trend Runs module — FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.trend_runs.repositories import TrendRunRepository
from app.modules.trend_runs.services import TrendRunService


async def get_trend_run_repository(db: AsyncSession = Depends(get_db)) -> TrendRunRepository:
    return TrendRunRepository(db)


async def get_trend_run_service(
    repo: TrendRunRepository = Depends(get_trend_run_repository),
) -> TrendRunService:
    return TrendRunService(repo)
