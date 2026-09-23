"""Add Social Media AI Agent foundation tables.

Revision ID: 0002_social_media_foundation
Revises: 0001_initial_schema
Create Date: 2026-08-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_social_media_foundation"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "social_organizations",
        *_common_columns(),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
    )
    op.create_index("ix_social_organizations_slug", "social_organizations", ["slug"], unique=False)

    op.create_table(
        "social_brand_kits",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("colors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fonts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tone", sa.Text(), nullable=True),
        sa.Column("guidelines", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_social_brand_kits_organization_id", "social_brand_kits", ["organization_id"])

    op.create_table(
        "social_connections",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("account_id", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("credential_ref", sa.String(500), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="disconnected"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("organization_id", "platform", "account_id", name="uq_social_connection_account"),
    )
    op.create_index("ix_social_connections_organization_id", "social_connections", ["organization_id"])

    op.create_table(
        "social_content_briefs",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_trend_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_prompt_package_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("campaign_type", sa.String(50), nullable=False, server_default="organic"),
        sa.Column("target_platforms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("target_audience", sa.Text(), nullable=True),
        sa.Column("tone", sa.String(100), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="id"),
        sa.Column("approval_policy", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("brief_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="queued"),
    )
    op.create_index("ix_social_content_briefs_organization_id", "social_content_briefs", ["organization_id"])
    op.create_index("ix_social_content_briefs_source_trend_id", "social_content_briefs", ["source_trend_id"])
    op.create_index("ix_social_content_briefs_source_prompt_package_id", "social_content_briefs", ["source_prompt_package_id"])
    op.create_index("ix_social_content_briefs_created_by", "social_content_briefs", ["created_by"])
    op.create_index("ix_social_content_briefs_status", "social_content_briefs", ["status"])

    op.create_table(
        "social_content_items",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("brief_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_content_briefs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concept", sa.Text(), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="draft"),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("content_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_social_content_items_organization_id", "social_content_items", ["organization_id"])
    op.create_index("ix_social_content_items_brief_id", "social_content_items", ["brief_id"])
    op.create_index("ix_social_content_items_status", "social_content_items", ["status"])

    op.create_table(
        "social_content_variants",
        *_common_columns(),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_content_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("format", sa.String(50), nullable=True),
        sa.Column("aspect_ratio", sa.String(20), nullable=True),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("hook", sa.Text(), nullable=True),
        sa.Column("cta", sa.Text(), nullable=True),
        sa.Column("hashtags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("media_ref", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("qa_status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("qa_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="draft"),
    )
    op.create_index("ix_social_content_variants_content_item_id", "social_content_variants", ["content_item_id"])
    op.create_index("ix_social_content_variants_platform", "social_content_variants", ["platform"])
    op.create_index("ix_social_content_variants_status", "social_content_variants", ["status"])

    op.create_table(
        "social_content_approvals",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_content_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_social_content_approvals_organization_id", "social_content_approvals", ["organization_id"])
    op.create_index("ix_social_content_approvals_content_item_id", "social_content_approvals", ["content_item_id"])

    op.create_table(
        "social_publish_jobs",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content_variant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_content_variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="queued"),
        sa.Column("external_post_id", sa.String(500), nullable=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False, unique=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("response_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_social_publish_jobs_organization_id", "social_publish_jobs", ["organization_id"])
    op.create_index("ix_social_publish_jobs_content_variant_id", "social_publish_jobs", ["content_variant_id"])
    op.create_index("ix_social_publish_jobs_status", "social_publish_jobs", ["status"])
    op.create_index("ix_social_publish_jobs_idempotency_key", "social_publish_jobs", ["idempotency_key"])


def downgrade() -> None:
    op.drop_table("social_publish_jobs")
    op.drop_table("social_content_approvals")
    op.drop_table("social_content_variants")
    op.drop_table("social_content_items")
    op.drop_table("social_content_briefs")
    op.drop_table("social_connections")
    op.drop_table("social_brand_kits")
    op.drop_table("social_organizations")
