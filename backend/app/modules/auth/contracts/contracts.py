"""Auth module — contracts (abstract interfaces)."""

from abc import ABC, abstractmethod
from typing import Optional
import uuid

from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


class AuthServiceContract(ABC):
    """Interface for the authentication service."""

    @abstractmethod
    async def register(self, data: RegisterRequest) -> AuthResponse:
        ...

    @abstractmethod
    async def login(self, data: LoginRequest) -> AuthResponse:
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserResponse]:
        ...
