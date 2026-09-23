"""Generic async CRUD repository.

Provides reusable data-access methods so that modules don't repeat
boilerplate SQLAlchemy queries. Each module creates a concrete
repository by subclassing BaseRepository with its model type.
"""

import uuid
from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.base_model import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Async CRUD repository for a given SQLAlchemy model."""

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    # -- Read -----------------------------------------------------------------

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[ModelType]:
        """Get a single record by ID (excludes soft-deleted)."""
        stmt = (
            select(self.model)
            .where(self.model.id == record_id)
            .where(self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[list[Any]] = None,
        order_by: Optional[Any] = None,
    ) -> Sequence[ModelType]:
        """Get a paginated list of records (excludes soft-deleted)."""
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        if filters:
            for f in filters:
                stmt = stmt.where(f)

        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.created_at.desc())

        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, *, filters: Optional[list[Any]] = None) -> int:
        """Count records matching optional filters (excludes soft-deleted)."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.deleted_at.is_(None))
        )
        if filters:
            for f in filters:
                stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # -- Write ----------------------------------------------------------------

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new record."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, record_id: uuid.UUID, data: dict[str, Any]) -> Optional[ModelType]:
        """Update a record by ID. Returns None if not found."""
        instance = await self.get_by_id(record_id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, record_id: uuid.UUID) -> bool:
        """Soft-delete a record by ID."""
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        instance.soft_delete()
        await self.session.flush()
        return True

    async def hard_delete(self, record_id: uuid.UUID) -> bool:
        """Permanently delete a record."""
        instance = await self.get_by_id(record_id)
        if instance is None:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True

    # -- Pagination helper ----------------------------------------------------

    async def paginate(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[list[Any]] = None,
        order_by: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Return paginated results with metadata."""
        total = await self.count(filters=filters)
        skip = (page - 1) * page_size
        items = await self.get_all(
            skip=skip,
            limit=page_size,
            filters=filters,
            order_by=order_by,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        }
