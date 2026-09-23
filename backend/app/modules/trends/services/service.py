"""Trends module — service."""

import uuid

from app.core.exceptions import InvalidStateTransitionException, NotFoundException
from app.modules.trends.enums import TrendStatus
from app.modules.trends.repositories import TrendRepository
from app.modules.trends.schemas import (
    PromptPackageSummaryResponse,
    TrendDetailResponse,
    TrendEvidenceResponse,
    TrendListResponse,
    TrendQueryParams,
    TrendReviewSummaryResponse,
    TrendSignalResponse,
)


class TrendService:
    def __init__(self, repo: TrendRepository) -> None:
        self.repo = repo

    async def query(self, params: TrendQueryParams) -> dict:
        result = await self.repo.query_trends(
            status=params.status,
            category=params.category,
            minimum_score=params.minimum_score,
            language=params.language,
            search=params.search,
            page=params.page,
            page_size=params.page_size,
        )
        result["items"] = [TrendListResponse.model_validate(t) for t in result["items"]]
        return result

    async def get_detail(self, trend_id: uuid.UUID) -> TrendDetailResponse:
        trend = await self.repo.get_detail(trend_id)
        if not trend:
            raise NotFoundException(message="Trend not found")

        # Build nested response
        signals = [TrendSignalResponse.model_validate(s) for s in (trend.signals or [])]
        evidence = [TrendEvidenceResponse.model_validate(e) for e in (trend.evidence or [])]
        reviews = [TrendReviewSummaryResponse.model_validate(r) for r in (trend.reviews or [])]

        # Latest prompt package
        latest_pp = None
        if trend.prompt_packages:
            sorted_pps = sorted(trend.prompt_packages, key=lambda p: p.version, reverse=True)
            latest_pp = PromptPackageSummaryResponse.model_validate(sorted_pps[0])

        return TrendDetailResponse(
            id=trend.id,
            title=trend.title,
            description=trend.description,
            core_concept=trend.core_concept,
            category=trend.category,
            status=trend.status,
            overall_score=trend.overall_score,
            risk_level=trend.risk_level,
            first_seen_at=trend.first_seen_at,
            last_seen_at=trend.last_seen_at,
            created_at=trend.created_at,
            updated_at=trend.updated_at,
            signals=signals,
            evidence=evidence,
            latest_prompt_package=latest_pp,
            reviews=reviews,
        )

    async def transition_status(self, trend_id: uuid.UUID, new_status: TrendStatus) -> None:
        """Validate and perform a status transition."""
        trend = await self.repo.get_by_id(trend_id)
        if not trend:
            raise NotFoundException(message="Trend not found")

        current = TrendStatus(trend.status)
        if not current.can_transition_to(new_status):
            raise InvalidStateTransitionException(
                message=f"Cannot transition from '{current.value}' to '{new_status.value}'"
            )

        await self.repo.update(trend_id, {"status": new_status.value})
