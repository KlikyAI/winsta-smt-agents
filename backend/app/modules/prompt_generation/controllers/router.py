"""Prompt Generation module — API router."""

import uuid

from fastapi import APIRouter, Depends, status

from app.core.responses import accepted_response, success_response
from app.modules.auth.dependencies import get_current_user, require_role
from app.modules.auth.enums import UserRole
from app.modules.prompt_generation.dependencies import get_prompt_generation_service
from app.modules.prompt_generation.services import PromptGenerationService

router = APIRouter(prefix="/trends/{trend_id}", tags=["Prompt Packages"])


@router.get("/prompt-packages")
async def get_prompt_packages(
    trend_id: uuid.UUID,
    service: PromptGenerationService = Depends(get_prompt_generation_service),
    _user=Depends(get_current_user),
):
    packages = await service.get_packages(trend_id)
    return success_response(data=[p.model_dump() for p in packages])


@router.get("/prompt-packages/latest")
async def get_latest_prompt_package(
    trend_id: uuid.UUID,
    service: PromptGenerationService = Depends(get_prompt_generation_service),
    _user=Depends(get_current_user),
):
    package = await service.get_latest(trend_id)
    return success_response(data=package.model_dump())


@router.get("/prompt")
async def get_prompt_for_integration(
    trend_id: uuid.UUID,
    service: PromptGenerationService = Depends(get_prompt_generation_service),
    _user=Depends(get_current_user),
):
    """Return the latest integration-ready prompt, including its public reference image URL."""
    package = await service.get_latest(trend_id)
    return success_response(data=package.model_dump())


@router.post("/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_prompt(
    trend_id: uuid.UUID,
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    """Trigger prompt regeneration via Celery."""
    try:
        from app.workers.ai_tasks import regenerate_prompt_package
        regenerate_prompt_package.delay(str(trend_id))
    except Exception:
        pass

    return accepted_response(
        data={"trend_id": str(trend_id)},
        message="Prompt regeneration queued",
    )
