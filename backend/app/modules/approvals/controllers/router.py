"""Approvals module — API router."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.responses import success_response
from app.modules.approvals.dependencies import get_approval_service
from app.modules.approvals.schemas import ReviewRequest
from app.modules.approvals.services import ApprovalService
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.auth.enums import UserRole
from app.modules.auth.models import User

router = APIRouter(tags=["Approvals"])


class BatchReviewRequest(BaseModel):
    trend_ids: list[uuid.UUID] = Field(..., min_length=1, description="List of trend IDs to review")
    decision: str = Field(..., description="approve | reject")
    notes: Optional[str] = Field(None, description="Optional batch review notes")


@router.post("/trends/{trend_id}/review")
async def review_trend(
    trend_id: uuid.UUID,
    data: ReviewRequest,
    service: ApprovalService = Depends(get_approval_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    """Process review decision for a single trend."""
    result = await service.review_trend(trend_id, data, current_user)
    return success_response(data=result.model_dump(), message=f"Trend {data.decision}d")


@router.post("/approvals/batch")
async def batch_review_trends(
    data: BatchReviewRequest,
    service: ApprovalService = Depends(get_approval_service),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER, UserRole.REVIEWER)),
):
    """Process batch review decisions across multiple selected trends."""
    result = await service.batch_review_trends(
        trend_ids=data.trend_ids,
        decision=data.decision,
        notes=data.notes,
        reviewer=current_user,
    )
    return success_response(
        data=result,
        message=f"Successfully processed {result['processed_count']} trends as '{result['status']}'",
    )
