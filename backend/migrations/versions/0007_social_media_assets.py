"""Add durable social media asset metadata.

Revision ID: 0007_social_media_assets
Revises: 0006_social_oauth_providers
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_social_media_assets"
down_revision = "0006_social_oauth_providers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "social_media_assets",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("storage_bucket", sa.String(length=100), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("media_type", sa.String(length=30), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("aspect_ratio", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ready"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["content_item_id"], ["social_content_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organization_id"], ["social_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "sha256", name="uq_social_media_asset_checksum"),
        sa.UniqueConstraint("storage_path"),
    )
    for column in ("id", "organization_id", "content_item_id", "media_type", "sha256", "status"):
        op.create_index(f"ix_social_media_assets_{column}", "social_media_assets", [column])

    op.add_column(
        "social_content_variants",
        sa.Column("media_asset_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_social_content_variants_media_asset_id",
        "social_content_variants",
        ["media_asset_id"],
    )
    op.create_foreign_key(
        "fk_social_content_variants_media_asset_id",
        "social_content_variants",
        "social_media_assets",
        ["media_asset_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_social_content_variants_media_asset_id",
        "social_content_variants",
        type_="foreignkey",
    )
    op.drop_index("ix_social_content_variants_media_asset_id", table_name="social_content_variants")
    op.drop_column("social_content_variants", "media_asset_id")
    op.drop_table("social_media_assets")
