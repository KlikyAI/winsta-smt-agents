"""Trend Runs module — service."""

import uuid
from datetime import datetime, timezone

import structlog

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.trend_runs.enums import TrendRunStatus
from app.modules.trend_runs.repositories import TrendRunRepository
from app.modules.trend_runs.schemas import (
    CreateTrendRunRequest,
    TrendRunQueuedResponse,
    TrendRunResponse,
)

logger = structlog.get_logger()


class TrendRunService:
    def __init__(self, repo: TrendRunRepository) -> None:
        self.repo = repo

    async def create_run(self, data: CreateTrendRunRequest) -> TrendRunQueuedResponse:
        """Create a trend run and dispatch to Celery (returns 202)."""
        categories_list = [data.category] if data.category else data.categories
        metadata = {
            "country": data.country or data.market,
            "category": data.category or (data.categories[0] if data.categories else "all"),
            "aesthetic": data.aesthetic or "minimalist_organic",
            "time_window": data.time_window or "24h",
        }

        run = await self.repo.create({
            "status": TrendRunStatus.QUEUED.value,
            "trigger_type": "manual",
            "sources": data.sources,
            "categories": categories_list,
            "market": (data.country or data.market).lower(),
            "language": data.language,
            "limit_per_source": data.limit_per_source,
            "metadata_": metadata,
        })

        # Dispatch Celery task
        try:
            from app.workers.collect_tasks import run_trend_discovery
            run_trend_discovery.delay(str(run.id))
        except Exception as e:
            logger.warning("celery_dispatch_failed", trend_run_id=str(run.id), error=str(e))

        logger.info("trend_run_created", trend_run_id=str(run.id), status=run.status)
        return TrendRunQueuedResponse(id=run.id, status=run.status)

    async def get_all(self, page: int = 1, page_size: int = 20) -> dict:
        result = await self.repo.paginate(page=page, page_size=page_size)
        result["items"] = [TrendRunResponse.model_validate(r) for r in result["items"]]
        return result

    async def get_by_id(self, run_id: uuid.UUID) -> TrendRunResponse:
        run = await self.repo.get_by_id(run_id)
        if not run:
            raise NotFoundException(message="Trend run not found")
        return TrendRunResponse.model_validate(run)

    async def cancel(self, run_id: uuid.UUID) -> TrendRunResponse:
        run = await self.repo.get_by_id(run_id)
        if not run:
            raise NotFoundException(message="Trend run not found")

        current_status = TrendRunStatus(run.status)
        if current_status.is_terminal:
            raise BadRequestException(message=f"Cannot cancel run in '{run.status}' status")

        updated = await self.repo.update(run_id, {
            "status": TrendRunStatus.CANCELLED.value,
            "completed_at": datetime.now(timezone.utc),
        })
        logger.info("trend_run_cancelled", trend_run_id=str(run_id))
        return TrendRunResponse.model_validate(updated)
