"""Approvals module — Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject|request_regeneration)$")
    notes: Optional[str] = None


class TrendReviewResponse(BaseModel):
    id: uuid.UUID
    trend_id: uuid.UUID
    reviewer_id: Optional[uuid.UUID] = None
    reviewer_name: Optional[str] = None
    decision: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
