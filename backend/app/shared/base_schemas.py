"""Common Pydantic schemas shared across modules."""

import uuid
from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response envelope."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class IdResponse(BaseModel):
    """Response containing just an ID."""
    id: uuid.UUID


class TimestampMixin(BaseModel):
    """Common timestamp fields for response schemas."""
    created_at: datetime
    updated_at: datetime


class SoftDeleteMixin(BaseModel):
    """Soft delete field for response schemas."""
    deleted_at: Optional[datetime] = None
