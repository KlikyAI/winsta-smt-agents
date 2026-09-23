"""Auth module — service implementation."""

import uuid
import re
from typing import Optional

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException, UnauthorizedException
from app.core.redis import get_redis
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.modules.auth.contracts import AuthServiceContract
from app.modules.auth.enums import UserRole
from app.modules.auth.repositories import OrganizationMembershipRepository, OrganizationRepository, UserRepository
from app.modules.social_media.models import SocialOrganization, SocialOrganizationMember
from app.modules.auth.schemas import (
    AuthResponse,
    CreateUserRequest,
    CreateWorkspaceRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateUserRequest,
    UserResponse,
    WorkspaceResponse,
)


class AuthService(AuthServiceContract):
    """Concrete implementation of auth operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, data: RegisterRequest) -> AuthResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise BadRequestException(message="Email already registered")

        user = await self.user_repo.create({
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "full_name": data.full_name,
            # Never allow public registration to self-assign an elevated role.
            "role": UserRole.VIEWER.value,
        })

        # Every new account starts with an isolated workspace. Provider OAuth
        # tokens and all social content are later resolved through this
        # organization boundary, never through a global credential.
        slug_base = re.sub(r"[^a-z0-9]+", "-", data.full_name.lower()).strip("-") or "workspace"
        workspace = SocialOrganization(
            slug=f"{slug_base}-{str(user.id).split('-', 1)[0]}",
            name=f"{data.full_name}'s Workspace",
            status="active",
        )
        self.user_repo.session.add(workspace)
        await self.user_repo.session.flush()
        self.user_repo.session.add(
            SocialOrganizationMember(
                organization_id=workspace.id,
                user_id=user.id,
                role="owner",
                status="active",
            )
        )

        tokens = await self._generate_tokens(user)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(self, data: LoginRequest) -> AuthResponse:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException(message="Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException(message="Account is deactivated")

        tokens = await self._generate_tokens(user)
        return AuthResponse(
            user=UserResponse.model_validate(user),
            tokens=tokens,
        )

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserResponse]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        return UserResponse.model_validate(user)

    async def list_users(self, *, search: str | None = None) -> list[UserResponse]:
        users = await self.user_repo.list_users(search=search)
        return [UserResponse.model_validate(user) for user in users]

    async def create_user(self, data: CreateUserRequest, *, actor_id: uuid.UUID) -> UserResponse:
        if await self.user_repo.get_by_email(data.email):
            raise ConflictException(message="A user with this email already exists")
        user = await self.user_repo.create(
            {
                "email": data.email,
                "hashed_password": hash_password(data.password),
                "full_name": data.full_name,
                "role": data.role.value,
                "is_active": True,
            }
        )
        # Provisioned team members must be attached to the administrator's
        # active workspace; otherwise they would have no tenant boundary.
        memberships = await OrganizationMembershipRepository(self.user_repo.session).list_for_user(actor_id)
        if memberships:
            self.user_repo.session.add(
                SocialOrganizationMember(
                    organization_id=memberships[0].organization_id,
                    user_id=user.id,
                    role="member",
                    status="active",
                )
            )
        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UpdateUserRequest,
        *,
        actor_id: uuid.UUID,
    ) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(message="User not found")

        changes = data.model_dump(exclude_unset=True)
        if "role" in changes:
            changes["role"] = changes["role"].value if isinstance(changes["role"], UserRole) else str(changes["role"])
        if "password" in changes:
            password = changes.pop("password")
            if password:
                changes["hashed_password"] = hash_password(password)

        if user.id == actor_id:
            if changes.get("is_active") is False:
                raise BadRequestException(message="You cannot deactivate your own account")
            if changes.get("role") and changes["role"] != user.role:
                raise BadRequestException(message="You cannot change your own role")

        # Do not let an admin accidentally remove the last active administrator.
        if user.role == UserRole.ADMIN.value and (
            changes.get("role") not in (None, UserRole.ADMIN.value) or changes.get("is_active") is False
        ):
            active_admins = await self.user_repo.list_users(include_inactive=False)
            if sum(1 for candidate in active_admins if candidate.role == UserRole.ADMIN.value) <= 1:
                raise BadRequestException(message="At least one active administrator is required")

        updated = await self.user_repo.update(user_id, changes)
        return UserResponse.model_validate(updated)

    async def list_workspaces(self, user_id: uuid.UUID) -> list[WorkspaceResponse]:
        memberships = await OrganizationMembershipRepository(self.user_repo.session).list_with_organizations(user_id)
        return [
            WorkspaceResponse(
                id=organization.id,
                slug=organization.slug,
                name=organization.name,
                status=organization.status,
                role=membership.role,
            )
            for membership, organization in memberships
        ]

    async def create_workspace(self, user_id: uuid.UUID, data: CreateWorkspaceRequest) -> WorkspaceResponse:
        """Create an isolated workspace and make the caller its owner."""
        slug = data.slug or re.sub(r"[^a-z0-9]+", "-", data.name.lower()).strip("-")
        slug = slug[:92].strip("-") or "workspace"
        if await OrganizationRepository(self.user_repo.session).get_by_slug(slug):
            raise ConflictException(message="A workspace with this slug already exists")

        workspace = SocialOrganization(slug=slug, name=data.name.strip(), status="active")
        self.user_repo.session.add(workspace)
        await self.user_repo.session.flush()
        self.user_repo.session.add(
            SocialOrganizationMember(
                organization_id=workspace.id,
                user_id=user_id,
                role="owner",
                status="active",
            )
        )
        return WorkspaceResponse(
            id=workspace.id,
            slug=workspace.slug,
            name=workspace.name,
            status=workspace.status,
            role="owner",
        )


    async def refresh_tokens(self, refresh_token_str: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token_str)
            if payload.get("type") != "refresh":
                raise UnauthorizedException(message="Invalid token type")
            user_id = uuid.UUID(payload.get("sub"))
            jti = str(payload["jti"])
        except Exception:
            raise UnauthorizedException(message="Invalid or expired refresh token")

        # Consume the refresh token atomically. A replayed token is rejected,
        # while a successful refresh receives a new one-time token.
        try:
            redis = await get_redis()
            consumed = await redis.getdel(f"auth:refresh:{jti}")
        except Exception:
            raise UnauthorizedException(message="Refresh service is temporarily unavailable")
        if not consumed:
            raise UnauthorizedException(message="Invalid or already-used refresh token")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException(message="User not found or inactive")

        return await self._generate_tokens(user)

    async def _generate_tokens(self, user) -> TokenResponse:
        token_data = {"sub": str(user.id), "role": user.role}
        refresh_token = create_refresh_token(token_data)
        refresh_payload = decode_token(refresh_token)
        try:
            redis = await get_redis()
            await redis.setex(
                f"auth:refresh:{refresh_payload['jti']}",
                10080 * 60 + 60,
                str(user.id),
            )
        except Exception:
            # Login remains available during a transient Redis outage, but a
            # refresh cannot succeed until a newly issued token is registered.
            pass
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=refresh_token,
        )
