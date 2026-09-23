"""Async SQLAlchemy database engine and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# Supabase transaction/session poolers do not preserve asyncpg prepared
# statements across backend connections. Disabling the statement cache keeps
# SQLAlchemy/asyncpg compatible with both pooler modes.
def _prepared_statement_name() -> str:
    """Return a unique prepared statement name for transaction poolers."""
    return f"__asyncpg_{uuid4()}__"


ASYNC_PG_CONNECT_ARGS = {
    "statement_cache_size": 0,
    "prepared_statement_name_func": _prepared_statement_name,
}

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args=ASYNC_PG_CONNECT_ARGS,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_celery_task_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides an isolated async database session for Celery worker tasks.

    Uses NullPool so connections are created and disposed cleanly within
    the task's asyncio event loop, preventing 'Event loop is closed' errors.
    """
    task_settings = get_settings()
    task_engine = create_async_engine(
        task_settings.database_url,
        echo=False,
        poolclass=NullPool,
        connect_args=ASYNC_PG_CONNECT_ARGS,
    )
    task_session_maker = async_sessionmaker(
        task_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with task_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
            await task_engine.dispose()
