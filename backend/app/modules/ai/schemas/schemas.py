"""AI module — Pydantic schemas."""

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AIExecutionResponse(BaseModel):
    id: uuid.UUID
    trend_id: Optional[uuid.UUID] = None
    provider: str
    model: str
    capability: str
    latency_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None
    status: str
    error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
