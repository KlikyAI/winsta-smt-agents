"""Add paid social campaign planning and approval records.

Revision ID: 0011_social_campaigns
Revises: 0010_workspace_memberships
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0011_social_campaigns"
down_revision: Union[str, None] = "0010_workspace_memberships"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "social_campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("objective", sa.String(100), nullable=False),
        sa.Column("platforms", postgresql.JSONB, nullable=False),
        sa.Column("budget_cents", sa.Integer, nullable=False, server_default="0"),
        sa.Column("budget_type", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("audience", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("creative_variant_ids", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("brief_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("provider_campaign_ids", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["social_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["brief_id"], ["social_content_briefs.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_social_campaigns_organization_id", "social_campaigns", ["organization_id"])
    op.create_index("ix_social_campaigns_status", "social_campaigns", ["status"])
    op.create_index("ix_social_campaigns_created_by", "social_campaigns", ["created_by"])
    op.create_index("ix_social_campaigns_approved_by", "social_campaigns", ["approved_by"])
    op.create_index("ix_social_campaigns_brief_id", "social_campaigns", ["brief_id"])


def downgrade() -> None:
    op.drop_index("ix_social_campaigns_brief_id", table_name="social_campaigns")
    op.drop_index("ix_social_campaigns_approved_by", table_name="social_campaigns")
    op.drop_index("ix_social_campaigns_created_by", table_name="social_campaigns")
    op.drop_index("ix_social_campaigns_status", table_name="social_campaigns")
    op.drop_index("ix_social_campaigns_organization_id", table_name="social_campaigns")
    op.drop_table("social_campaigns")
