"""Trend Candidates module — TrendCandidate model."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel
import app.modules.trend_runs.models  # noqa: F401


class TrendCandidate(BaseModel):
    """Raw or normalized candidate discovered from an external source.

    The raw_payload JSONB column preserves the original provider response
    before any normalization — we never throw away the original data.
    """

    __tablename__ = "trend_candidates"

    trend_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trend_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trend_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="raw", index=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True, index=True)
    canonical_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    author_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    view_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engagement_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    trend_run = relationship("TrendRun", back_populates="candidates")
