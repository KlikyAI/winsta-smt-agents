"""Trend Runs module — Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Request schemas ---------------------------------------------------------

class CreateTrendRunRequest(BaseModel):
    sources: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    market: str = "global"
    country: Optional[str] = None
    category: Optional[str] = None
    aesthetic: Optional[str] = None
    time_window: Optional[str] = None
    language: str = "en"
    limit_per_source: int = Field(default=100, ge=1, le=1000)


# -- Candidate item schema for run detail ------------------------------------

class CandidateItemSchema(BaseModel):
    id: uuid.UUID
    platform: str
    status: str
    title: Optional[str] = None
    caption: Optional[str] = None
    canonical_url: Optional[str] = None
    author_name: Optional[str] = None
    engagement_rate: Optional[float] = None
    hashtags: Optional[list[str]] = None

    model_config = {"from_attributes": True}


# -- Response schemas --------------------------------------------------------

class TrendRunResponse(BaseModel):
    id: uuid.UUID
    status: str
    trigger_type: str
    sources: Optional[list[str]] = None
    categories: Optional[list[str]] = None
    market: Optional[str] = None
    language: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    candidate_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    error_count: int = 0
    metadata: Optional[dict[str, Any]] = Field(default=None, validation_alias="metadata_")
    candidates: list[CandidateItemSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class TrendRunQueuedResponse(BaseModel):
    """Minimal response for 202 Accepted."""
    id: uuid.UUID
    status: str
