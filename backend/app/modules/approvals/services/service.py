"""Approvals module — service."""

import uuid
from typing import Any, Optional
import structlog

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.approvals.repositories import TrendReviewRepository
from app.modules.approvals.schemas import ReviewRequest, TrendReviewResponse
from app.modules.auth.models import User
from app.modules.trends.enums import TrendStatus
from app.modules.trends.repositories import TrendRepository

logger = structlog.get_logger()


class ApprovalService:
    def __init__(
        self,
        review_repo: TrendReviewRepository,
        trend_repo: TrendRepository,
    ) -> None:
        self.review_repo = review_repo
        self.trend_repo = trend_repo

    async def review_trend(
        self,
        trend_id: uuid.UUID,
        data: ReviewRequest,
        reviewer: User,
    ) -> TrendReviewResponse:
        """Process a review decision for a single trend."""
        trend = await self.trend_repo.get_by_id(trend_id)
        if not trend:
            raise NotFoundException(message="Trend not found")

        # Determine new status
        status_map = {
            "approve": TrendStatus.APPROVED,
            "approved": TrendStatus.APPROVED,
            "reject": TrendStatus.REJECTED,
            "rejected": TrendStatus.REJECTED,
            "request_regeneration": TrendStatus.PROMPT_GENERATED,
        }
        dec = data.decision.lower()
        if dec not in status_map:
            raise BadRequestException(message=f"Invalid review decision '{data.decision}'")

        new_status = status_map[dec]
        current_status = _workflow_status(trend.status)
        if not current_status.can_transition_to(new_status):
            raise BadRequestException(
                message=f"Cannot transition trend from '{trend.status}' to '{new_status.value}'"
            )

        # Create immutable review record
        review = await self.review_repo.create({
            "trend_id": trend_id,
            "reviewer_id": reviewer.id,
            "reviewer_name": reviewer.full_name,
            "decision": dec,
            "notes": data.notes,
        })

        # Update trend status
        await self.trend_repo.update(trend_id, {"status": new_status.value})

        logger.info(
            "trend_reviewed",
            trend_id=str(trend_id),
            decision=dec,
            reviewer=reviewer.full_name,
            new_status=new_status.value,
        )

        # If approved, dispatch integration delivery
        if dec in ("approve", "approved"):
            try:
                from app.workers.integration_tasks import deliver_approved_trend
                deliver_approved_trend.delay(str(trend_id))
            except Exception as e:
                logger.warning("integration_dispatch_failed", error=str(e))
        elif dec == "request_regeneration":
            try:
                from app.workers.ai_tasks import regenerate_prompt_package
                regenerate_prompt_package.delay(str(trend_id))
            except Exception as e:
                logger.warning("prompt_regeneration_dispatch_failed", error=str(e))

        return TrendReviewResponse.model_validate(review)

    async def batch_review_trends(
        self,
        trend_ids: list[uuid.UUID],
        decision: str,
        notes: Optional[str],
        reviewer: User,
    ) -> dict[str, Any]:
        """Process batch review decisions across multiple trends."""
        dec = decision.lower()
        status_map = {
            "approve": TrendStatus.APPROVED,
            "approved": TrendStatus.APPROVED,
            "reject": TrendStatus.REJECTED,
            "rejected": TrendStatus.REJECTED,
        }
        if dec not in status_map:
            raise BadRequestException(message=f"Invalid batch decision '{decision}'. Must be 'approve' or 'reject'.")

        new_status = status_map[dec]
        processed = []
        errors = []

        for tid in trend_ids:
            try:
                trend = await self.trend_repo.get_by_id(tid)
                if not trend:
                    errors.append({"trend_id": str(tid), "error": "Not found"})
                    continue

                current_status = _workflow_status(trend.status)
                if not current_status.can_transition_to(new_status):
                    errors.append({
                        "trend_id": str(tid),
                        "error": f"Cannot transition from '{trend.status}' to '{new_status.value}'",
                    })
                    continue

                # Create review log
                await self.review_repo.create({
                    "trend_id": tid,
                    "reviewer_id": reviewer.id,
                    "reviewer_name": reviewer.full_name,
                    "decision": dec,
                    "notes": notes or f"Batch {dec} operation",
                })

                # Update trend status
                await self.trend_repo.update(tid, {"status": new_status.value})
                processed.append(str(tid))

                # Dispatch if approved
                if dec in ("approve", "approved"):
                    try:
                        from app.workers.integration_tasks import deliver_approved_trend
                        deliver_approved_trend.delay(str(tid))
                    except Exception:
                        pass
            except Exception as e:
                errors.append({"trend_id": str(tid), "error": str(e)})

        logger.info(
            "batch_trends_reviewed",
            count=len(processed),
            decision=dec,
            reviewer=reviewer.full_name,
        )

        return {
            "processed_count": len(processed),
            "processed_ids": processed,
            "errors": errors,
            "status": new_status.value,
        }


def _workflow_status(value: str) -> TrendStatus:
    """Read the legacy plural prompt status written by older workers."""
    if value == "prompts_generated":
        return TrendStatus.PENDING_REVIEW
    return TrendStatus(value)
