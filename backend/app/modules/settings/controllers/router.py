"""Settings module — API router."""

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.core.responses import success_response
from app.modules.auth.dependencies import require_role
from app.modules.auth.enums import UserRole
from app.modules.settings.schemas import SystemSettingsResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=None)
async def get_system_settings(
    _user=Depends(require_role(UserRole.ADMIN, UserRole.TREND_MANAGER)),
):
    settings = get_settings()
    data = SystemSettingsResponse(
        app_name=settings.app_name,
        app_env=settings.app_env,
        ai_provider=settings.ai_provider,
        ai_model=settings.ai_model,
        ai_fallback_provider=settings.ai_fallback_provider,
        ai_fallback_model=settings.ai_fallback_model,
        scoring_threshold=settings.scoring_threshold,
        default_limit_per_source=settings.default_limit_per_source,
        discovery_schedule_minutes=settings.discovery_schedule_minutes,
    )
    return success_response(data=data.model_dump())
