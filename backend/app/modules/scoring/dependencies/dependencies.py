"""Scoring module — FastAPI dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.scoring.repositories import ScoringConfigurationRepository, TrendSignalRepository
from app.modules.scoring.services import ScoringService


async def get_scoring_config_repository(db: AsyncSession = Depends(get_db)) -> ScoringConfigurationRepository:
    return ScoringConfigurationRepository(db)


async def get_trend_signal_repository(db: AsyncSession = Depends(get_db)) -> TrendSignalRepository:
    return TrendSignalRepository(db)


async def get_scoring_service(
    config_repo: ScoringConfigurationRepository = Depends(get_scoring_config_repository),
    signal_repo: TrendSignalRepository = Depends(get_trend_signal_repository),
) -> ScoringService:
    return ScoringService(config_repo, signal_repo)
