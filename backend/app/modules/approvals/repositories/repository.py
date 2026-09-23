"""Approvals module — repository."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.approvals.models import TrendReview
from app.shared.base_repository import BaseRepository


class TrendReviewRepository(BaseRepository[TrendReview]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(TrendReview, session)
