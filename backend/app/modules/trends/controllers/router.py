"""Trends module — API router."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.responses import success_response
from app.modules.auth.dependencies import get_current_user
from app.modules.trends.dependencies import get_trend_service
from app.modules.trends.schemas import TrendQueryParams
from app.modules.trends.services import TrendService

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("")
async def list_trends(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    minimum_score: Optional[float] = Query(None),
    language: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: TrendService = Depends(get_trend_service),
    _user=Depends(get_current_user),
):
    params = TrendQueryParams(
        status=status,
        category=category,
        source=source,
        minimum_score=minimum_score,
        language=language,
        search=search,
        page=page,
        page_size=page_size,
    )
    result = await service.query(params)
    result["items"] = [t.model_dump() for t in result["items"]]
    return success_response(data=result)


@router.get("/{trend_id}")
async def get_trend_detail(
    trend_id: uuid.UUID,
    service: TrendService = Depends(get_trend_service),
    _user=Depends(get_current_user),
):
    result = await service.get_detail(trend_id)
    return success_response(data=result.model_dump())
