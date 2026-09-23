"""Auth module — repository."""

from typing import Optional

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
from app.modules.social_media.models import SocialOrganization, SocialOrganizationMember
from app.shared.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        stmt = (
            select(User)
            .where(User.email == email)
            .where(User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        *,
        search: str | None = None,
        include_inactive: bool = True,
    ) -> list[User]:
        """Return users for the admin directory, excluding soft-deleted rows."""
        stmt = select(User).where(User.deleted_at.is_(None))
        if not include_inactive:
            stmt = stmt.where(User.is_active.is_(True))
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(or_(User.email.ilike(pattern), User.full_name.ilike(pattern)))
        stmt = stmt.order_by(User.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OrganizationMembershipRepository(BaseRepository[SocialOrganizationMember]):
    """Queries for authenticated users' tenant/workspace memberships."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SocialOrganizationMember, session)

    async def list_for_user(self, user_id: uuid.UUID) -> list[SocialOrganizationMember]:
        result = await self.session.execute(
            select(SocialOrganizationMember)
            .where(SocialOrganizationMember.user_id == user_id)
            .where(SocialOrganizationMember.status == "active")
            .where(SocialOrganizationMember.deleted_at.is_(None))
            .order_by(SocialOrganizationMember.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_with_organizations(
        self,
        user_id: uuid.UUID,
    ) -> list[tuple[SocialOrganizationMember, SocialOrganization]]:
        result = await self.session.execute(
            select(SocialOrganizationMember, SocialOrganization)
            .join(SocialOrganization, SocialOrganization.id == SocialOrganizationMember.organization_id)
            .where(SocialOrganizationMember.user_id == user_id)
            .where(SocialOrganizationMember.status == "active")
            .where(SocialOrganizationMember.deleted_at.is_(None))
            .where(SocialOrganization.status == "active")
            .where(SocialOrganization.deleted_at.is_(None))
            .order_by(SocialOrganizationMember.created_at.asc())
        )
        return list(result.all())

    async def get_for_user_and_organization(
        self,
        *,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> SocialOrganizationMember | None:
        result = await self.session.execute(
            select(SocialOrganizationMember)
            .where(SocialOrganizationMember.user_id == user_id)
            .where(SocialOrganizationMember.organization_id == organization_id)
            .where(SocialOrganizationMember.status == "active")
            .where(SocialOrganizationMember.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()


class OrganizationRepository(BaseRepository[SocialOrganization]):
    """Workspace lookup repository kept separate from social connections."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SocialOrganization, session)

    async def get_by_slug(self, slug: str) -> SocialOrganization | None:
        result = await self.session.execute(
            select(SocialOrganization)
            .where(SocialOrganization.slug == slug)
            .where(SocialOrganization.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()
