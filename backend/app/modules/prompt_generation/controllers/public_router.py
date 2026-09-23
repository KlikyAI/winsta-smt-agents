"""Unauthenticated read-only API for validated trend prompt packages."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response

from app.core.responses import success_response
from app.core.rate_limit import rate_limit
from app.modules.prompt_generation.dependencies import get_prompt_generation_service
from app.modules.prompt_generation.services import PromptGenerationService


public_router = APIRouter(prefix="/public/prompts", tags=["Public Prompt API"])


@public_router.get("")
async def list_public_prompts(
    response: Response,
    date_from: date | None = Query(None, description="Inclusive creation date (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Inclusive creation date (YYYY-MM-DD)"),
    category: str | None = Query(None, min_length=1, max_length=100),
    search: str | None = Query(None, min_length=2, max_length=200),
    has_reference_image: bool | None = Query(None),
    min_quality_score: float | None = Query(None, ge=0, le=100),
    generation_mode: str | None = Query(None, min_length=1, max_length=50),
    latest_only: bool = Query(True, description="Return only the latest passed version per trend"),
    sort: Literal["newest", "oldest", "quality_desc"] = Query("newest"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: PromptGenerationService = Depends(get_prompt_generation_service),
    _rate_limit=Depends(rate_limit("public:prompts", limit=60, window_seconds=60)),
):
    """List integration-ready prompt packages without an access token."""
    result = await service.list_public(
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        category=category,
        search=search,
        has_reference_image=has_reference_image,
        min_quality_score=min_quality_score,
        generation_mode=generation_mode,
        latest_only=latest_only,
        sort=sort,
    )
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return success_response(data=result.model_dump())
