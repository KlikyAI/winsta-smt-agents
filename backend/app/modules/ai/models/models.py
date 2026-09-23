"""AI module — AIExecution model."""

import uuid
from typing import Any, Optional

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class AIExecution(BaseModel):
    """Log of an individual AI provider call.

    Records provider, model, capability, latency, token counts,
    estimated cost, and any errors for observability.
    """

    __tablename__ = "ai_executions"

    trend_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    capability: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="success")
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    request_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    response_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
