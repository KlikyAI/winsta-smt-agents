"""Trend Sources module — TrendSource model."""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class TrendSource(BaseModel):
    """Represents a configured trend discovery source (e.g., Instagram, TikTok)."""

    __tablename__ = "trend_sources"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    collector_type: Mapped[str] = mapped_column(String(50), nullable=False, default="api")
    configuration: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
