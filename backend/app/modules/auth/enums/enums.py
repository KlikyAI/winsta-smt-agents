"""Auth module enums."""

from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    TREND_MANAGER = "trend_manager"
    REVIEWER = "reviewer"
    VIEWER = "viewer"

    @property
    def label(self) -> str:
        return {
            UserRole.ADMIN: "Administrator",
            UserRole.TREND_MANAGER: "Trend Manager",
            UserRole.REVIEWER: "Reviewer",
            UserRole.VIEWER: "Viewer",
        }[self]

    @property
    def permissions(self) -> list[str]:
        """Return permissions for this role."""
        base = ["read:trends", "read:sources"]
        if self == UserRole.VIEWER:
            return base
        if self == UserRole.REVIEWER:
            return base + ["review:trends"]
        if self == UserRole.TREND_MANAGER:
            return base + ["review:trends", "manage:trends", "manage:sources", "manage:scoring"]
        if self == UserRole.ADMIN:
            return base + [
                "review:trends", "manage:trends", "manage:sources",
                "manage:scoring", "manage:users", "manage:settings",
            ]
        return base
