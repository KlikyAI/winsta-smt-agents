"""Trend Sources module — Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Request schemas ---------------------------------------------------------

class UpdateTrendSourceRequest(BaseModel):
    name: Optional[str] = None
    collector_type: Optional[str] = None
    configuration: Optional[dict[str, Any]] = None


class CreateTrendSourceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=50)
    collector_type: str = "api"
    configuration: Optional[dict[str, Any]] = None
    enabled: bool = True


# -- Response schemas --------------------------------------------------------

class TrendSourceResponse(BaseModel):
    """Response schema exposing source details and configuration metadata."""
    id: uuid.UUID
    name: str
    platform: str
    enabled: bool
    collector_type: str
    configuration: Optional[dict[str, Any]] = None
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrendSourceDetailResponse(TrendSourceResponse):
    """Detail response."""
    pass
