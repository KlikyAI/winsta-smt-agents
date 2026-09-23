"""Add tenant/workspace memberships for SaaS isolation.

Revision ID: 0010_social_workspace_memberships
Revises: 0009_prompt_reference_image
Create Date: 2026-08-30 00:00:00.000000
"""

import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0010_workspace_memberships"
down_revision: Union[str, None] = "0009_prompt_reference_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "social_organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(30), nullable=False, server_default="member"),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["social_organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_social_organization_member"),
    )
    op.create_index(
        "ix_social_organization_members_organization_id",
        "social_organization_members",
        ["organization_id"],
    )
    op.create_index(
        "ix_social_organization_members_user_id",
        "social_organization_members",
        ["user_id"],
    )
    op.create_index(
        "ix_social_organization_members_status",
        "social_organization_members",
        ["status"],
    )

    # Preserve the existing single-tenant deployment. Existing users are
    # attached to the Winsta workspace so their working connections remain
    # visible after the tenant boundary is enabled.
    bind = op.get_bind()
    default_workspace = bind.execute(
        sa.text(
            "SELECT id FROM social_organizations "
            "WHERE slug = 'winsta' AND deleted_at IS NULL"
        )
    ).scalar_one_or_none()
    if default_workspace is None:
        default_workspace = uuid.uuid4()
        bind.execute(
            sa.text(
                "INSERT INTO social_organizations "
                "(id, slug, name, status) "
                "VALUES (:id, 'winsta', 'Winsta AI', 'active')"
            ),
            {"id": default_workspace},
        )
    existing_users = bind.execute(
        sa.text(
            """
            SELECT org.id, u.id, u.role
            FROM users u
            CROSS JOIN social_organizations org
            WHERE org.slug = 'winsta'
              AND u.deleted_at IS NULL
            """
        )
    ).fetchall()
    for organization_id, user_id, user_role in existing_users:
        bind.execute(
            sa.text(
                """
                INSERT INTO social_organization_members
                    (id, organization_id, user_id, role, status)
                VALUES (:id, :organization_id, :user_id, :role, 'active')
                ON CONFLICT (organization_id, user_id) DO NOTHING
                """
            ),
            {
                "id": uuid.uuid4(),
                "organization_id": organization_id,
                "user_id": user_id,
                "role": "owner" if user_role == "admin" else "member",
            },
        )


def downgrade() -> None:
    op.drop_index("ix_social_organization_members_status", table_name="social_organization_members")
    op.drop_index("ix_social_organization_members_user_id", table_name="social_organization_members")
    op.drop_index("ix_social_organization_members_organization_id", table_name="social_organization_members")
    op.drop_table("social_organization_members")
