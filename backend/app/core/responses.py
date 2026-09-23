"""Standardized API response envelope.

Mirrors Medicare's WebResponseUtils::base() pattern:
  { "message": "...", "data": ... }
"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    message: str = ""
    data: Optional[T] = None


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
) -> dict[str, Any]:
    """Build a success response dict. Use as return value from route handlers."""
    return {"message": message, "data": data}


def created_response(
    data: Any = None,
    message: str = "Created",
) -> dict[str, Any]:
    """Build a 201 Created response dict."""
    return {"message": message, "data": data}


def accepted_response(
    data: Any = None,
    message: str = "Accepted",
) -> dict[str, Any]:
    """Build a 202 Accepted response dict."""
    return {"message": message, "data": data}
