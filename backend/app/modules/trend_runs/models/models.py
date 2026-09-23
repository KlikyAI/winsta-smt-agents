"""Trend Runs module — TrendRun model."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel
import app.modules.trend_candidates.models  # noqa: F401


class TrendRun(BaseModel):
    """Represents a single trend discovery execution."""

    __tablename__ = "trend_runs"

    status: Mapped[str] = mapped_column(String(50), nullable=False, default="queued", index=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    sources: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    categories: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    market: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="global")
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="en")
    limit_per_source: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=100)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    # Relationships
    candidates = relationship("TrendCandidate", back_populates="trend_run", lazy="selectin")
