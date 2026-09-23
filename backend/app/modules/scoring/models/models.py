"""Scoring module — ScoringConfiguration and TrendSignal models."""

import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class ScoringConfiguration(BaseModel):
    """Configurable scoring weights.

    Each row represents a signal type and its weight.
    Weights should sum to 100 across all active configurations.
    Versioned to support history tracking.
    """

    __tablename__ = "scoring_configurations"

    signal_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TrendSignal(BaseModel):
    """Individual scoring signal computed for a Trend.

    Each signal represents one dimension of the trend's score
    (e.g., freshness=85, velocity=72). The final overall_score on
    Trend is the weighted sum of these signals.
    """

    __tablename__ = "trend_signals"

    trend_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trends.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    normalized_value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "deterministic" or "ai"

    # Relationships
    trend = relationship("Trend", back_populates="signals")
