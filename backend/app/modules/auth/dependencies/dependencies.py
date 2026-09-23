"""Auth module — FastAPI dependencies for DI and authorization.

Mirrors Medicare's middleware pattern: authenticate via JWT, then
check role-based access with specific dependency functions.
"""

import uuid
from typing import Annotated

from fastapi import Depends, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.modules.auth.enums import UserRole
from app.modules.auth.models import User
from app.modules.auth.repositories import OrganizationMembershipRepository, OrganizationRepository, UserRepository
from app.modules.auth.services import AuthService


# -- Service DI ---------------------------------------------------------------

async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)


# -- Auth dependencies --------------------------------------------------------

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Invalid authorization header")

    token = authorization.removeprefix("Bearer ")
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException(message="Invalid token type")
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise UnauthorizedException(message="Invalid or expired token")

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(message="User not found or inactive")

    return user


async def get_optional_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Return the authenticated user when a bearer token is present.

    OAuth callbacks are intentionally public and resolve their workspace from
    the signed/hashed OAuth state. This optional dependency lets the shared
    social service remain usable by that callback while scoping normal API
    requests to the caller's workspace.
    """
    if not authorization:
        return None
    return await get_current_user(authorization=authorization, db=db)


async def get_current_organization_id(
    current_user: User | None = Depends(get_optional_current_user),
    organization_header: Annotated[str | None, Header(alias="X-Organization-ID")] = None,
    db: AsyncSession = Depends(get_db),
) -> uuid.UUID | None:
    """Resolve the active workspace for an authenticated request.

    Clients may explicitly select a workspace with ``X-Organization-ID``.
    Without the header, the first active membership is used, preserving the
    existing single-workspace UX while enabling multi-tenant accounts.
    """
    if current_user is None:
        return None

    memberships = OrganizationMembershipRepository(db)
    if organization_header:
        try:
            organization_id = uuid.UUID(organization_header)
        except ValueError as exc:
            raise ForbiddenException(message="Invalid X-Organization-ID header") from exc
        membership = await memberships.get_for_user_and_organization(
            user_id=current_user.id,
            organization_id=organization_id,
        )
        if not membership:
            raise ForbiddenException(message="You do not have access to this workspace")
        organization = await OrganizationRepository(db).get_by_id(organization_id)
        if not organization or organization.status != "active":
            raise ForbiddenException(message="Workspace is not active")
        return organization_id

    available = await memberships.list_for_user(current_user.id)
    if available:
        return available[0].organization_id

    # Compatibility fallback for deployments that have not run the workspace
    # backfill migration yet. It can be removed after all environments reach
    # migration 0010.
    organization = await OrganizationRepository(db).get_by_slug("winsta")
    return organization.id if organization else None


def require_role(*allowed_roles: UserRole):
    """FastAPI dependency factory that checks user role.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        try:
            user_role = UserRole(current_user.role)
        except ValueError as exc:
            raise ForbiddenException(message="User has an invalid role") from exc
        if user_role not in allowed_roles:
            raise ForbiddenException(
                message=f"Role '{current_user.role}' does not have access to this resource"
            )
        return current_user

    return _check_role


def require_permission(permission: str):
    """FastAPI dependency factory for permission-based authorization.

    Permissions are derived centrally from ``UserRole`` so API handlers do
    not need to duplicate role matrices and new roles remain auditable.
    """
    async def _check_permission(current_user: User = Depends(get_current_user)) -> User:
        try:
            role = UserRole(current_user.role)
        except ValueError as exc:
            raise ForbiddenException(message="User has an invalid role") from exc
        if permission not in role.permissions:
            raise ForbiddenException(message=f"Permission '{permission}' is required")
        return current_user

    return _check_permission
