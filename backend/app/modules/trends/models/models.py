"""Trends module — Trend and TrendEvidence models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel
import app.modules.scoring.models  # noqa: F401
import app.modules.prompt_generation.models  # noqa: F401
import app.modules.approvals.models  # noqa: F401


class Trend(BaseModel):
    """Canonical deduplicated trend concept.

    Multiple TrendCandidates from different platforms may map to a
    single Trend via TrendEvidence.
    """

    __tablename__ = "trends"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    core_concept: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="discovered",
        index=True,
    )
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    first_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    evidence = relationship("TrendEvidence", back_populates="trend", lazy="selectin")
    signals = relationship("TrendSignal", back_populates="trend", lazy="selectin")
    prompt_packages = relationship("PromptPackage", back_populates="trend", lazy="selectin")
    reviews = relationship("TrendReview", back_populates="trend", lazy="selectin")


class TrendEvidence(BaseModel):
    """Links a Trend to its source TrendCandidates.

    Multiple candidates across platforms can contribute evidence to
    a single canonical Trend.
    """

    __tablename__ = "trend_evidence"

    trend_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trends.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trend_candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    trend = relationship("Trend", back_populates="evidence")
