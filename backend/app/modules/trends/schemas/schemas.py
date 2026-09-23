"""Trends module — Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# -- Request schemas ---------------------------------------------------------

class TrendQueryParams(BaseModel):
    """Query parameters for trend listing."""
    status: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    minimum_score: Optional[float] = None
    language: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# -- Response schemas --------------------------------------------------------

class TrendSignalResponse(BaseModel):
    signal_type: str
    raw_value: float
    normalized_value: float
    weight: float
    weighted_score: float
    source: Optional[str] = None

    model_config = {"from_attributes": True}


class TrendEvidenceResponse(BaseModel):
    id: uuid.UUID
    trend_candidate_id: uuid.UUID
    platform: str
    relevance_score: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PromptPackageSummaryResponse(BaseModel):
    id: uuid.UUID
    version: int
    quality_score: Optional[float] = None
    validation_status: Optional[str] = None
    generated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TrendReviewSummaryResponse(BaseModel):
    id: uuid.UUID
    reviewer_name: Optional[str] = None
    decision: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendListResponse(BaseModel):
    """Compact trend for list views."""
    id: uuid.UUID
    title: str
    category: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TrendDetailResponse(BaseModel):
    """Full trend detail with nested data."""
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    core_concept: Optional[str] = None
    category: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    risk_level: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # Nested data
    signals: list[TrendSignalResponse] = []
    evidence: list[TrendEvidenceResponse] = []
    latest_prompt_package: Optional[PromptPackageSummaryResponse] = None
    reviews: list[TrendReviewSummaryResponse] = []

    model_config = {"from_attributes": True}
