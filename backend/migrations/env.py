"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig
from uuid import uuid4

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import get_settings
from app.core.database import Base

# Import all models so Alembic can detect them
from app.modules.auth.models import User  # noqa
from app.modules.trend_sources.models import TrendSource  # noqa
from app.modules.trend_runs.models import TrendRun  # noqa
from app.modules.trend_candidates.models import TrendCandidate  # noqa
from app.modules.trends.models import Trend, TrendEvidence  # noqa
from app.modules.scoring.models import ScoringConfiguration, TrendSignal  # noqa
from app.modules.prompt_generation.models import PromptPackage  # noqa
from app.modules.approvals.models import TrendReview  # noqa
from app.modules.ai.models import AIExecution  # noqa
from app.modules.integrations.models import IntegrationDelivery  # noqa
from app.modules.social_media.models import (  # noqa
    BrandKit,
    SocialCampaign,
    ContentApproval,
    ContentBrief,
    ContentItem,
    ContentVariant,
    PublishJob,
    SocialCredential,
    SocialConnection,
    SocialMetricSnapshot,
    SocialOAuthState,
    SocialOrganization,
    SocialOrganizationMember,
)

config = context.config
settings = get_settings()

# Runtime uses the transaction-mode pooler. Migrations may opt into the
# direct/session-mode URL supplied as DIRECT_URL.
migration_url = settings.direct_url or settings.database_url
# Alembic uses ConfigParser interpolation, so percent-encoded credentials must
# be escaped before being written into sqlalchemy.url.
config.set_main_option("sqlalchemy.url", migration_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _prepared_statement_name() -> str:
    return f"__asyncpg_{uuid4()}__"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_name_func": _prepared_statement_name,
        },
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
