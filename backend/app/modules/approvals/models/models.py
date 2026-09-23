"""Approvals module — TrendReview model."""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class TrendReview(BaseModel):
    """Audit log entry for trend approval/rejection decisions.

    Every review action is stored as an immutable record for
    auditability. A trend can have multiple reviews (e.g., reject
    then re-review and approve).
    """

    __tablename__ = "trend_reviews"

    trend_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trends.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False)  # approve | reject | request_regeneration
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    trend = relationship("Trend", back_populates="reviews")
