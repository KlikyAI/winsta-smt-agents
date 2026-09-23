"""Auth module — API router."""

import uuid

from fastapi import APIRouter, Depends, status

from app.core.responses import success_response
from app.core.rate_limit import rate_limit
from app.modules.auth.dependencies import get_auth_service, get_current_user, require_permission
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    AuthResponse,
    CreateUserRequest,
    CreateWorkspaceRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    UpdateUserRequest,
    UserResponse,
)
from app.modules.auth.services import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
    _rate_limit=Depends(rate_limit("auth:register", limit=5, window_seconds=3600)),
):
    result = await service.register(data)
    return success_response(data=result.model_dump(), message="Registration successful")


@router.post("/login")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
    _rate_limit=Depends(rate_limit("auth:login", limit=10, window_seconds=60)),
):
    result = await service.login(data)
    return success_response(data=result.model_dump(), message="Login successful")


@router.post("/refresh")
async def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.refresh_tokens(data.refresh_token)
    return success_response(data=result.model_dump(), message="Token refreshed successfully")


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    user_data = UserResponse.model_validate(current_user)
    return success_response(data=user_data.model_dump(), message="User profile retrieved")


@router.get("/users")
async def list_users(
    search: str | None = None,
    _admin: User = Depends(require_permission("manage:users")),
    service: AuthService = Depends(get_auth_service),
):
    """List users visible to platform administrators."""
    users = await service.list_users(search=search)
    return success_response(
        data=[user.model_dump() for user in users],
        message="Users retrieved",
    )


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: CreateUserRequest,
    admin: User = Depends(require_permission("manage:users")),
    service: AuthService = Depends(get_auth_service),
):
    user = await service.create_user(data, actor_id=admin.id)
    return success_response(data=user.model_dump(), message="User created")


@router.patch("/users/{user_id}")
async def update_user(
    user_id: uuid.UUID,
    data: UpdateUserRequest,
    admin: User = Depends(require_permission("manage:users")),
    service: AuthService = Depends(get_auth_service),
):
    user = await service.update_user(user_id, data, actor_id=admin.id)
    return success_response(data=user.model_dump(), message="User updated")


@router.get("/workspaces")
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """List workspaces the user may select with ``X-Organization-ID``."""
    workspaces = await service.list_workspaces(current_user.id)
    return success_response(
        data=[workspace.model_dump() for workspace in workspaces],
        message="Workspaces retrieved",
    )


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    workspace = await service.create_workspace(current_user.id, data)
    return success_response(data=workspace.model_dump(), message="Workspace created")
