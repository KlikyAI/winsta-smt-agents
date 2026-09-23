"""Add provider-specific OAuth state metadata.

Revision ID: 0006_social_oauth_providers
Revises: 0005_social_omnichannel
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_social_oauth_providers"
down_revision = "0005_social_omnichannel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "social_oauth_states",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("social_oauth_states", "metadata")
