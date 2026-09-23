"""Settings module — schemas."""

from typing import Optional
from pydantic import BaseModel


class SystemSettingsResponse(BaseModel):
    app_name: str
    app_env: str
    ai_provider: str
    ai_model: str
    ai_fallback_provider: Optional[str] = None
    ai_fallback_model: Optional[str] = None
    scoring_threshold: float
    default_limit_per_source: int
    discovery_schedule_minutes: int
