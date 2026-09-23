"""Prompt Generation module — PromptPackage model."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class PromptPackage(BaseModel):
    """Generated prompt package for a scored trend across 6 AI modalities.

    Supports:
    1. Text to Image
    2. Text to Video
    3. Text to Voice (Script & TTS directives)
    4. Image to Image (Remix / Style transfer)
    5. Image to Video (Motion directives)
    6. Video to Video (V2V style transfer)
    """

    __tablename__ = "prompt_packages"

    trend_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trends.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    trend_title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    core_concept: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    generation_modes: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # 6 AI Modality Prompts
    text_to_image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Backward compatible alias
    text_to_video_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_to_voice_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_to_image_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_to_video_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_to_video_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trend_reference_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_flags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    # AI metadata
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    template_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    validation_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="pending")

    # Relationships
    trend = relationship("Trend", back_populates="prompt_packages")
