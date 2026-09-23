"""Scoring module — API router."""

from fastapi import APIRouter, Depends

from app.core.responses import success_response
from app.modules.auth.dependencies import require_role
from app.modules.auth.enums import UserRole
from app.modules.scoring.dependencies import get_scoring_service
from app.modules.scoring.schemas import UpdateScoringSettingsRequest
from app.modules.scoring.services import ScoringService

router = APIRouter(prefix="/scoring", tags=["Scoring"])


@router.get("/settings")
async def get_scoring_settings(
    service: ScoringService = Depends(get_scoring_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.get_settings()
    return success_response(data=result.model_dump())


@router.put("/settings")
async def update_scoring_settings(
    data: UpdateScoringSettingsRequest,
    service: ScoringService = Depends(get_scoring_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.update_settings(data)
    return success_response(data=result.model_dump(), message="Scoring settings updated")
