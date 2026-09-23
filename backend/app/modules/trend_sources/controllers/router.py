"""Trend Sources module — API router."""

import uuid

from fastapi import APIRouter, Depends

from app.core.responses import success_response
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.auth.enums import UserRole
from app.modules.trend_sources.dependencies import get_trend_source_service
from app.modules.trend_sources.schemas import UpdateTrendSourceRequest
from app.modules.trend_sources.services import TrendSourceService

router = APIRouter(prefix="/trend-sources", tags=["Trend Sources"])


@router.get("")
async def list_sources(
    service: TrendSourceService = Depends(get_trend_source_service),
    _user=Depends(get_current_user),
):
    sources = await service.get_all()
    return success_response(data=[s.model_dump() for s in sources])


@router.get("/{source_id}")
async def get_source(
    source_id: uuid.UUID,
    service: TrendSourceService = Depends(get_trend_source_service),
    _user=Depends(get_current_user),
):
    source = await service.get_by_id(source_id)
    return success_response(data=source.model_dump())


@router.patch("/{source_id}")
async def update_source(
    source_id: uuid.UUID,
    data: UpdateTrendSourceRequest,
    service: TrendSourceService = Depends(get_trend_source_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    source = await service.update(source_id, data)
    return success_response(data=source.model_dump(), message="Source updated")


@router.post("/{source_id}/enable")
async def enable_source(
    source_id: uuid.UUID,
    service: TrendSourceService = Depends(get_trend_source_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    source = await service.enable(source_id)
    return success_response(data=source.model_dump(), message="Source enabled")


@router.post("/{source_id}/disable")
async def disable_source(
    source_id: uuid.UUID,
    service: TrendSourceService = Depends(get_trend_source_service),
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    source = await service.disable(source_id)
    return success_response(data=source.model_dump(), message="Source disabled")
