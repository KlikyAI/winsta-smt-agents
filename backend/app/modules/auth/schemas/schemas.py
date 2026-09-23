"""Auth module — Pydantic schemas."""

import uuid
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.modules.auth.enums import UserRole


# -- Request schemas ---------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=1, max_length=255)
    # Public self-registration is always a viewer.  The field is retained for
    # backwards-compatible clients, but the service never trusts it.
    role: str = "viewer"


class CreateUserRequest(BaseModel):
    """Payload used by an administrator to provision a team member."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=3, max_length=100)

    @field_validator("slug")
    @classmethod
    def valid_slug(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError("slug must contain lowercase letters, numbers, and hyphens only")
        return value


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


# -- Response schemas --------------------------------------------------------

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse


class WorkspaceResponse(BaseModel):
    """Workspace visible to the authenticated user."""

    id: uuid.UUID
    slug: str
    name: str
    status: str
    role: str
