"""Trend Runs module — API router."""

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.responses import accepted_response, success_response
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.auth.enums import UserRole
from app.modules.trend_runs.dependencies import get_trend_run_service
from app.modules.trend_runs.schemas import CreateTrendRunRequest
from app.modules.trend_runs.services import TrendRunService

router = APIRouter(prefix="/trend-runs", tags=["Trend Runs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_trend_run(
    data: CreateTrendRunRequest,
    service: TrendRunService = Depends(get_trend_run_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.create_run(data)
    return accepted_response(data=result.model_dump(), message="Trend run queued")


@router.get("")
async def list_trend_runs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TrendRunService = Depends(get_trend_run_service),
    _user=Depends(get_current_user),
):
    result = await service.get_all(page=page, page_size=page_size)
    result["items"] = [r.model_dump() for r in result["items"]]
    return success_response(data=result)


@router.get("/{run_id}")
async def get_trend_run(
    run_id: uuid.UUID,
    service: TrendRunService = Depends(get_trend_run_service),
    _user=Depends(get_current_user),
):
    result = await service.get_by_id(run_id)
    return success_response(data=result.model_dump())


@router.post("/{run_id}/cancel")
async def cancel_trend_run(
    run_id: uuid.UUID,
    service: TrendRunService = Depends(get_trend_run_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    result = await service.cancel(run_id)
    return success_response(data=result.model_dump(), message="Trend run cancelled")
