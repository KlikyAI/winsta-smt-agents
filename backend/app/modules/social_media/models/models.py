"""Persistence models for the Social Media AI Agent.

The first release is configured for Winsta, while every tenant-owned record
already carries an organization boundary for a later multi-tenant rollout.
"""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class SocialOrganization(BaseModel):
    __tablename__ = "social_organizations"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")

    brand_kits = relationship("BrandKit", back_populates="organization", lazy="selectin")
    performance_insights = relationship(
        "SocialPerformanceInsight", back_populates="organization", lazy="selectin"
    )
    connections = relationship("SocialConnection", back_populates="organization", lazy="selectin")
    briefs = relationship("ContentBrief", back_populates="organization", lazy="selectin")
    members = relationship(
        "SocialOrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    campaigns = relationship("SocialCampaign", back_populates="organization", lazy="selectin")


class SocialOrganizationMember(BaseModel):
    """A user's membership in a tenant/workspace.

    Social credentials and content remain organization-owned.  Memberships
    only determine which authenticated users may select and manage a
    workspace; they never contain provider tokens.
    """

    __tablename__ = "social_organization_members"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_social_organization_member"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)

    organization = relationship("SocialOrganization", back_populates="members")


class SocialCampaign(BaseModel):
    """Tenant-owned paid campaign plan and approval record.

    This model deliberately stores the approved plan separately from provider
    campaign IDs. Provider launch/update operations can be added later without
    bypassing the approval boundary or mixing paid and organic content jobs.
    """

    __tablename__ = "social_campaigns"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(String(100), nullable=False)
    platforms: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    budget_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    budget_type: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    audience: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    creative_variant_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    brief_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_briefs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_campaign_ids: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization = relationship("SocialOrganization", back_populates="campaigns")


class BrandKit(BaseModel):
    __tablename__ = "social_brand_kits"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, default="Winsta AI")
    tagline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    colors: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    fonts: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_hashtags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    disclaimer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    forbidden_terms: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    required_terms: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    product_facts: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    languages: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=lambda: ["id", "en", "ar"])
    guidelines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    organization = relationship("SocialOrganization", back_populates="brand_kits")


class SocialConnection(BaseModel):
    __tablename__ = "social_connections"
    __table_args__ = (UniqueConstraint("organization_id", "platform", "account_id", name="uq_social_connection_account"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credential_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scopes: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="disconnected")
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    organization = relationship("SocialOrganization", back_populates="connections")


class SocialCredential(BaseModel):
    __tablename__ = "social_credentials"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    credential_type: Mapped[str] = mapped_column(String(50), nullable=False, default="oauth2")
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)


class SocialOAuthState(BaseModel):
    __tablename__ = "social_oauth_states"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    redirect_uri: Mapped[str] = mapped_column(String(1000), nullable=False)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class SocialMetricSnapshot(BaseModel):
    __tablename__ = "social_metric_snapshots"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    publish_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_publish_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    external_post_id: Mapped[str] = mapped_column(String(500), nullable=False)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SocialPerformanceInsight(BaseModel):
    """Materialized learning output derived from the latest metric snapshot per post."""

    __tablename__ = "social_performance_insights"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    content_format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    performance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    engagement_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    organization = relationship("SocialOrganization", back_populates="performance_insights")


class SocialMediaAsset(BaseModel):
    __tablename__ = "social_media_assets"
    __table_args__ = (
        UniqueConstraint("organization_id", "sha256", name="uq_social_media_asset_checksum"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_item_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_items.id", ondelete="SET NULL"), nullable=True, index=True
    )
    storage_bucket: Mapped[str] = mapped_column(String(100), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    media_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="ready", index=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSONB, nullable=True)

    content_item = relationship("ContentItem", back_populates="media_assets")
    variants = relationship("ContentVariant", back_populates="media_asset", lazy="selectin")


class ContentBrief(BaseModel):
    __tablename__ = "social_content_briefs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_trend_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    source_prompt_package_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    campaign_type: Mapped[str] = mapped_column(String(50), nullable=False, default="organic")
    target_platforms: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    target_languages: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=lambda: ["en"])
    approval_policy: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    brief_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued", index=True)

    organization = relationship("SocialOrganization", back_populates="briefs")
    content_items = relationship(
        "ContentItem", back_populates="brief", cascade="all, delete-orphan", lazy="selectin"
    )


class ContentItem(BaseModel):
    __tablename__ = "social_content_items"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brief_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_briefs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", index=True)
    ai_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    brief = relationship("ContentBrief", back_populates="content_items")
    variants = relationship(
        "ContentVariant", back_populates="content_item", cascade="all, delete-orphan", lazy="selectin"
    )
    approvals = relationship(
        "ContentApproval", back_populates="content_item", cascade="all, delete-orphan", lazy="selectin"
    )
    media_assets = relationship("SocialMediaAsset", back_populates="content_item", lazy="selectin")


class ContentVariant(BaseModel):
    __tablename__ = "social_content_variants"
    __table_args__ = (
        UniqueConstraint(
            "content_item_id",
            "platform",
            "language",
            name="uq_social_content_variant_target",
        ),
    )

    content_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_media_assets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en", index=True)
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    aspect_ratio: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cta: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hashtags: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    media_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    visual_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    qa_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    qa_result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="draft", index=True)

    content_item = relationship("ContentItem", back_populates="variants")
    media_asset = relationship("SocialMediaAsset", back_populates="variants")
    publish_jobs = relationship("PublishJob", back_populates="content_variant", lazy="selectin")


class ContentApproval(BaseModel):
    __tablename__ = "social_content_approvals"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variant_ids: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    payload_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    content_item = relationship("ContentItem", back_populates="approvals")


class PublishJob(BaseModel):
    __tablename__ = "social_publish_jobs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_variant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_content_variants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="queued", index=True)
    external_post_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    content_variant = relationship("ContentVariant", back_populates="publish_jobs")
