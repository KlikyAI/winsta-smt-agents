"""Set English as the default Social Media content language.

Revision ID: 0003_social_default_english
Revises: 0002_social_media_foundation
Create Date: 2026-08-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0003_social_default_english"
down_revision: Union[str, None] = "0002_social_media_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("social_content_briefs", "language", server_default="en")


def downgrade() -> None:
    op.alter_column("social_content_briefs", "language", server_default="id")
