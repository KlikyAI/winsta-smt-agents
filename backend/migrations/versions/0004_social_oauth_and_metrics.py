"""Add encrypted OAuth credentials, OAuth state, and metric snapshots.

Revision ID: 0004_social_oauth_metrics
Revises: 0003_social_default_english
Create Date: 2026-08-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_social_oauth_metrics"
down_revision: Union[str, None] = "0003_social_default_english"
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
        "social_credentials",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("credential_type", sa.String(50), nullable=False, server_default="oauth2"),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_social_credentials_organization_id", "social_credentials", ["organization_id"])
    op.create_index("ix_social_credentials_status", "social_credentials", ["status"])

    op.create_table(
        "social_oauth_states",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("state_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("redirect_uri", sa.String(1000), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_social_oauth_states_organization_id", "social_oauth_states", ["organization_id"])
    op.create_index("ix_social_oauth_states_created_by", "social_oauth_states", ["created_by"])
    op.create_index("ix_social_oauth_states_state_hash", "social_oauth_states", ["state_hash"], unique=True)
    op.create_index("ix_social_oauth_states_expires_at", "social_oauth_states", ["expires_at"])

    op.create_table(
        "social_metric_snapshots",
        *_common_columns(),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("publish_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("social_publish_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("external_post_id", sa.String(500), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_social_metric_snapshots_organization_id", "social_metric_snapshots", ["organization_id"])
    op.create_index("ix_social_metric_snapshots_publish_job_id", "social_metric_snapshots", ["publish_job_id"])
    op.create_index("ix_social_metric_snapshots_platform", "social_metric_snapshots", ["platform"])
    op.create_index("ix_social_metric_snapshots_captured_at", "social_metric_snapshots", ["captured_at"])


def downgrade() -> None:
    op.drop_table("social_metric_snapshots")
    op.drop_table("social_oauth_states")
    op.drop_table("social_credentials")
