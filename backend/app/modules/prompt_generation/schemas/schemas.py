"""Prompt Generation module — Pydantic schemas for 6 AI modalities."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PromptPackageResponse(BaseModel):
    id: uuid.UUID
    trend_id: uuid.UUID
    version: int
    trend_title: str
    description: Optional[str] = None
    core_concept: Optional[str] = None
    category: Optional[str] = None
    generation_modes: Optional[list[str]] = None

    # 6 AI Modalities
    text_to_image_prompt: Optional[str] = None
    image_prompt: Optional[str] = None
    text_to_video_prompt: Optional[str] = None
    text_to_voice_prompt: Optional[str] = None
    image_to_image_prompt: Optional[str] = None
    image_to_video_prompt: Optional[str] = None
    video_to_video_prompt: Optional[str] = None

    negative_prompt: Optional[str] = None
    trend_reference_image_url: Optional[str] = None
    tags: Optional[list[str]] = None
    quality_score: Optional[float] = None
    risk_flags: Optional[list[str]] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    template_version: Optional[str] = None
    generated_at: Optional[datetime] = None
    validation_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptPackageGeneratedOutput(BaseModel):
    """Validated AI output structure for prompt packages supporting 6 modalities.

    All AI output is validated through this schema before storage.
    """
    trend_title: str
    description: str = ""
    core_concept: str = ""
    category: str = ""
    generation_modes: list[str] = Field(default_factory=list)

    # 6 AI Modality Outputs
    text_to_image_prompt: str = ""
    image_prompt: str = ""
    text_to_video_prompt: str = ""
    text_to_voice_prompt: str = ""
    image_to_image_prompt: str = ""
    image_to_video_prompt: str = ""
    video_to_video_prompt: str = ""

    negative_prompt: str = ""
    tags: list[str] = Field(default_factory=list)
    quality_score: float = 0.0
    risk_flags: list[str] = Field(default_factory=list)


class PublicPromptResponse(BaseModel):
    """Stable public contract; excludes internal risk and provider metadata."""

    id: uuid.UUID
    trend_id: uuid.UUID
    version: int
    trend_title: str
    description: Optional[str] = None
    core_concept: Optional[str] = None
    category: Optional[str] = None
    generation_modes: Optional[list[str]] = None
    text_to_image_prompt: Optional[str] = None
    image_prompt: Optional[str] = None
    text_to_video_prompt: Optional[str] = None
    text_to_voice_prompt: Optional[str] = None
    image_to_image_prompt: Optional[str] = None
    image_to_video_prompt: Optional[str] = None
    video_to_video_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    trend_reference_image_url: Optional[str] = None
    tags: Optional[list[str]] = None
    quality_score: Optional[float] = None
    generated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublicPromptPage(BaseModel):
    items: list[PublicPromptResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
