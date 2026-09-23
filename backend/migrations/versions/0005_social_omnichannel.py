"""Add multilingual omnichannel generation and reliable scheduling fields.

Revision ID: 0005_social_omnichannel
Revises: 0004_social_oauth_metrics
Create Date: 2026-08-25 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0005_social_omnichannel"
down_revision: Union[str, None] = "0004_social_oauth_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "social_content_briefs",
        sa.Column(
            "target_languages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"en\"]'::jsonb"),
        ),
    )
    op.execute(
        "UPDATE social_content_briefs "
        "SET target_languages = jsonb_build_array(language)"
    )

    op.add_column(
        "social_content_variants",
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
    )
    op.add_column("social_content_variants", sa.Column("visual_prompt", sa.Text(), nullable=True))
    op.add_column(
        "social_content_variants",
        sa.Column("generation_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index(
        "ix_social_content_variants_language",
        "social_content_variants",
        ["language"],
    )
    op.create_unique_constraint(
        "uq_social_content_variant_target",
        "social_content_variants",
        ["content_item_id", "platform", "language"],
    )

    op.add_column(
        "social_content_approvals",
        sa.Column("variant_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.add_column(
        "social_publish_jobs",
        sa.Column("timezone", sa.String(64), nullable=False, server_default="UTC"),
    )
    op.add_column(
        "social_publish_jobs",
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "social_publish_jobs",
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "social_publish_jobs",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_social_publish_jobs_next_attempt_at",
        "social_publish_jobs",
        ["next_attempt_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_social_publish_jobs_next_attempt_at", table_name="social_publish_jobs")
    op.drop_column("social_publish_jobs", "last_attempt_at")
    op.drop_column("social_publish_jobs", "next_attempt_at")
    op.drop_column("social_publish_jobs", "max_attempts")
    op.drop_column("social_publish_jobs", "timezone")
    op.drop_column("social_content_approvals", "variant_ids")
    op.drop_constraint(
        "uq_social_content_variant_target",
        "social_content_variants",
        type_="unique",
    )
    op.drop_index("ix_social_content_variants_language", table_name="social_content_variants")
    op.drop_column("social_content_variants", "generation_metadata")
    op.drop_column("social_content_variants", "visual_prompt")
    op.drop_column("social_content_variants", "language")
    op.drop_column("social_content_briefs", "target_languages")
