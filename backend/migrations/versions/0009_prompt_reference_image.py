"""Add a durable public reference image URL to prompt packages.

Revision ID: 0009_prompt_reference_image
Revises: 0008_social_brand_optimizer
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_prompt_reference_image"
down_revision = "0008_social_brand_optimizer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_packages", sa.Column("trend_reference_image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("prompt_packages", "trend_reference_image_url")
