"""Approvals module — dependencies."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.approvals.repositories import TrendReviewRepository
from app.modules.approvals.services import ApprovalService
from app.modules.trends.repositories import TrendRepository


async def get_review_repository(db: AsyncSession = Depends(get_db)) -> TrendReviewRepository:
    return TrendReviewRepository(db)


async def get_approval_service(
    review_repo: TrendReviewRepository = Depends(get_review_repository),
    db: AsyncSession = Depends(get_db),
) -> ApprovalService:
    trend_repo = TrendRepository(db)
    return ApprovalService(review_repo, trend_repo)
