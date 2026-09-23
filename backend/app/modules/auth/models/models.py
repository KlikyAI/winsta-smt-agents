"""Auth module — User model."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.auth.enums import UserRole
from app.shared.base_model import BaseModel


class User(BaseModel):
    """Internal user for the Prompt Trends Automation system."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.VIEWER.value,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
