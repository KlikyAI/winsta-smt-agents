"""API schemas for the Social Media AI Agent foundation."""

import uuid
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.modules.social_media.enums import (
    CampaignBudgetType,
    CampaignStatus,
    ContentApprovalDecision,
    SocialPlatform,
)


class CreateContentBriefRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    objective: Optional[str] = None
    campaign_type: str = Field(default="organic", max_length=50)
    target_platforms: list[SocialPlatform] = Field(min_length=1)
    target_audience: Optional[str] = None
    tone: Optional[str] = Field(default=None, max_length=100)
    language: Optional[str] = Field(default=None, min_length=2, max_length=10)
    languages: Optional[list[str]] = Field(default=None, min_length=1, max_length=3)
    source_trend_id: Optional[uuid.UUID] = None
    source_prompt_package_id: Optional[uuid.UUID] = None
    brief_data: Optional[dict[str, Any]] = None
    media_url: Optional[HttpUrl] = None
    generate_image: bool = True
    image_model: str = Field(default="flux-realism", max_length=50)
    visual_prompt: Optional[str] = Field(default=None, max_length=4000)

    @field_validator("target_platforms")
    @classmethod
    def unique_platforms(cls, value: list[SocialPlatform]) -> list[SocialPlatform]:
        if len(set(value)) != len(value):
            raise ValueError("target_platforms must not contain duplicates")
        return value

    @model_validator(mode="after")
    def normalize_languages(self) -> "CreateContentBriefRequest":
        requested = self.languages or ([self.language] if self.language else ["en"])
        normalized = [str(value).lower().split("-")[0] for value in requested]
        supported = {"id", "en", "ar"}
        unsupported = sorted(set(normalized) - supported)
        if unsupported:
            raise ValueError("languages must only contain id, en, or ar")
        if len(set(normalized)) != len(normalized):
            raise ValueError("languages must not contain duplicates")
        self.languages = normalized
        self.language = normalized[0]
        return self


class CreateCampaignRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    objective: str = Field(min_length=1, max_length=100)
    platforms: list[SocialPlatform] = Field(min_length=1, max_length=7)
    budget_cents: int = Field(ge=0, le=100_000_000_00)
    budget_type: CampaignBudgetType = CampaignBudgetType.DAILY
    currency: str = Field(default="USD", min_length=3, max_length=3)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    audience: dict[str, Any] = Field(default_factory=dict)
    creative_variant_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    brief_id: Optional[uuid.UUID] = None
    notes: Optional[str] = Field(default=None, max_length=4000)

    @field_validator("platforms")
    @classmethod
    def unique_platforms(cls, value: list[SocialPlatform]) -> list[SocialPlatform]:
        if len(set(value)) != len(value):
            raise ValueError("platforms must not contain duplicates")
        return value

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateCampaignRequest":
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValueError("end_at must be later than start_at")
        return self


class CampaignDecisionRequest(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=4000)


class CampaignStatusRequest(BaseModel):
    status: CampaignStatus
    notes: Optional[str] = Field(default=None, max_length=4000)


class ApproveContentRequest(BaseModel):
    decision: ContentApprovalDecision
    notes: Optional[str] = None
    variant_ids: Optional[list[uuid.UUID]] = Field(default=None, min_length=1)


class ScheduleContentRequest(BaseModel):
    scheduled_at: Optional[datetime] = None
    variant_ids: Optional[list[uuid.UUID]] = None
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @field_validator("scheduled_at")
    @classmethod
    def timezone_aware_schedule(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is not None and value.tzinfo is None:
            raise ValueError("scheduled_at must include a timezone offset")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value


class UpdateContentVariantRequest(BaseModel):
    caption: Optional[str] = Field(default=None, max_length=63206)
    hook: Optional[str] = Field(default=None, max_length=5000)
    cta: Optional[str] = Field(default=None, max_length=5000)
    hashtags: Optional[list[str]] = Field(default=None, max_length=30)
    media_ref: Optional[HttpUrl] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UpdateContentVariantRequest":
        if not self.model_fields_set:
            raise ValueError("At least one variant field must be provided")
        return self


class ReschedulePublishJobRequest(BaseModel):
    scheduled_at: datetime
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @field_validator("scheduled_at")
    @classmethod
    def timezone_aware_schedule(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("scheduled_at must include a timezone offset")
        return value

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        return value


class SocialBriefQueuedResponse(BaseModel):
    id: uuid.UUID
    status: str


class ContentVariantResponse(BaseModel):
    id: uuid.UUID
    platform: str
    language: str
    format: Optional[str] = None
    aspect_ratio: Optional[str] = None
    caption: Optional[str] = None
    hook: Optional[str] = None
    cta: Optional[str] = None
    hashtags: Optional[list[str]] = None
    media_ref: Optional[str] = None
    media_asset_id: Optional[uuid.UUID] = None
    visual_prompt: Optional[str] = None
    generation_metadata: Optional[dict[str, Any]] = None
    version: int
    qa_status: str
    qa_result: Optional[dict[str, Any]] = None
    status: str

    model_config = {"from_attributes": True}


class ContentItemResponse(BaseModel):
    id: uuid.UUID
    brief_id: uuid.UUID
    concept: Optional[str] = None
    status: str
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    content_data: Optional[dict[str, Any]] = None
    variants: list[ContentVariantResponse] = []

    model_config = {"from_attributes": True}


class ContentBriefResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    source_trend_id: Optional[uuid.UUID] = None
    source_prompt_package_id: Optional[uuid.UUID] = None
    title: str
    objective: Optional[str] = None
    campaign_type: str
    target_platforms: list[str]
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    language: str
    target_languages: list[str]
    status: str
    brief_data: Optional[dict[str, Any]] = None
    content_items: list[ContentItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SocialCampaignResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    name: str
    objective: str
    platforms: list[str]
    budget_cents: int
    budget_type: str
    currency: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    audience: dict[str, Any]
    creative_variant_ids: list[str]
    brief_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None
    provider_campaign_ids: dict[str, Any]
    status: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PublishJobResponse(BaseModel):
    id: uuid.UUID
    content_variant_id: uuid.UUID
    platform: str
    scheduled_at: Optional[datetime] = None
    timezone: str
    status: str
    idempotency_key: str
    attempt_count: int
    max_attempts: int
    next_attempt_at: Optional[datetime] = None
    last_attempt_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = {"from_attributes": True}


class SocialContentQueueItemResponse(ContentItemResponse):
    brief_title: str
    target_platforms: list[str]
    created_at: datetime
    updated_at: datetime


class SocialPublishQueueItemResponse(PublishJobResponse):
    brief_title: str
    content_item_id: uuid.UUID
    caption: Optional[str] = None
    hook: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SocialConnectionAccountResponse(BaseModel):
    id: uuid.UUID
    platform: str
    account_id: str
    account_name: Optional[str] = None
    scopes: Optional[list[str]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SocialPlatformConnectionResponse(BaseModel):
    platform: str
    display_name: str
    description: str
    setup_url: str
    callback_url: str
    requested_scopes: list[str]
    status: str
    missing_settings: list[str]
    accounts: list[SocialConnectionAccountResponse]


class BeginSocialConnectionResponse(BaseModel):
    platform: str
    status: str
    message: str
    callback_url: str
    authorization_url: Optional[str] = None
    missing_settings: list[str] = Field(default_factory=list)


class SocialOAuthProviderDiagnosticResponse(BaseModel):
    platform: str
    display_name: str
    server_configured: bool
    missing_settings: list[str]
    manual_checks: list[str]


class SocialOAuthDiagnosticsResponse(BaseModel):
    automatic_checks_passed: bool
    callback_url: str
    frontend_return_url: str
    callback_https: bool
    token_encryption_ready: bool
    issues: list[str]
    providers: list[SocialOAuthProviderDiagnosticResponse]


class SocialMetricSnapshotResponse(BaseModel):
    id: uuid.UUID
    publish_job_id: uuid.UUID
    platform: str
    external_post_id: str
    metrics: dict[str, Any]
    captured_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateBrandKitRequest(BaseModel):
    brand_name: str = Field(min_length=1, max_length=255)
    tagline: Optional[str] = Field(default=None, max_length=1000)
    logo_url: Optional[str] = Field(default=None, max_length=2000)
    colors: dict[str, str] = Field(default_factory=dict)
    fonts: dict[str, str] = Field(default_factory=dict)
    tone: Optional[str] = Field(default=None, max_length=2000)
    target_audience: Optional[str] = Field(default=None, max_length=4000)
    default_hashtags: list[str] = Field(default_factory=list, max_length=30)
    disclaimer: Optional[str] = Field(default=None, max_length=2000)
    forbidden_terms: list[str] = Field(default_factory=list, max_length=100)
    required_terms: list[str] = Field(default_factory=list, max_length=100)
    product_facts: dict[str, Any] = Field(default_factory=dict)
    languages: list[str] = Field(default_factory=lambda: ["id", "en", "ar"], min_length=1, max_length=3)
    guidelines: Optional[str] = Field(default=None, max_length=10000)

    @field_validator("default_hashtags")
    @classmethod
    def normalize_hashtags(cls, value: list[str]) -> list[str]:
        normalized = []
        for item in value:
            tag = item.strip().replace(" ", "")
            if tag:
                normalized.append(tag if tag.startswith("#") else f"#{tag}")
        return list(dict.fromkeys(normalized))

    @field_validator("forbidden_terms", "required_terms")
    @classmethod
    def normalize_terms(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @field_validator("languages")
    @classmethod
    def supported_languages(cls, value: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(item.lower().split("-")[0] for item in value))
        if set(normalized) - {"id", "en", "ar"}:
            raise ValueError("languages must only contain id, en, or ar")
        return normalized


class BrandKitResponse(UpdateBrandKitRequest):
    id: uuid.UUID
    organization_id: uuid.UUID
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SocialPerformanceInsightResponse(BaseModel):
    id: uuid.UUID
    platform: Optional[str] = None
    language: Optional[str] = None
    content_format: Optional[str] = None
    sample_size: int
    performance_score: float
    engagement_rate: float
    confidence: float
    summary: str
    recommendations: list[dict[str, Any]]
    evidence: dict[str, Any]
    status: str
    analyzed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class SocialMediaAssetResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    content_item_id: Optional[uuid.UUID] = None
    storage_bucket: str
    storage_path: str
    source_url: Optional[str] = None
    signed_url: Optional[str] = None
    mime_type: str
    media_type: str
    size_bytes: int
    sha256: str
    provider: Optional[str] = None
    prompt: Optional[str] = None
    aspect_ratio: Optional[str] = None
    status: str
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
