"""Add Brand Brain fields and materialized performance insights.

Revision ID: 0008_social_brand_optimizer
Revises: 0007_social_media_assets
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_social_brand_optimizer"
down_revision = "0007_social_media_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "social_brand_kits",
        sa.Column("brand_name", sa.String(length=255), nullable=False, server_default="Winsta AI"),
    )
    op.add_column("social_brand_kits", sa.Column("tagline", sa.Text(), nullable=True))
    op.add_column("social_brand_kits", sa.Column("target_audience", sa.Text(), nullable=True))
    op.add_column(
        "social_brand_kits",
        sa.Column(
            "default_hashtags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column("social_brand_kits", sa.Column("disclaimer", sa.Text(), nullable=True))
    op.add_column(
        "social_brand_kits",
        sa.Column(
            "forbidden_terms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "social_brand_kits",
        sa.Column(
            "required_terms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )
    op.add_column(
        "social_brand_kits",
        sa.Column(
            "product_facts",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "social_brand_kits",
        sa.Column(
            "languages",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[\"id\", \"en\", \"ar\"]'::jsonb"),
        ),
    )

    op.create_table(
        "social_performance_insights",
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("content_format", sa.String(length=50), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("performance_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "recommendations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["social_organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "id",
        "organization_id",
        "platform",
        "language",
        "content_format",
        "status",
        "analyzed_at",
    ):
        op.create_index(
            f"ix_social_performance_insights_{column}",
            "social_performance_insights",
            [column],
        )


def downgrade() -> None:
    op.drop_table("social_performance_insights")
    for column in (
        "languages",
        "product_facts",
        "required_terms",
        "forbidden_terms",
        "disclaimer",
        "default_hashtags",
        "target_audience",
        "tagline",
        "brand_name",
    ):
        op.drop_column("social_brand_kits", column)
