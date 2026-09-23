"""Prompt Trends Automation — FastAPI Application Factory.

Modular monolith backend for trend discovery, analysis, scoring,
prompt generation, and downstream handoff.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import register_middleware
from app.core.redis import close_redis, get_redis

# Import all SQLAlchemy models so relationships and mappers are registered at startup
import app.modules.auth.models  # noqa: F401
import app.modules.trend_sources.models  # noqa: F401
import app.modules.trend_runs.models  # noqa: F401
import app.modules.trend_candidates.models  # noqa: F401
import app.modules.trends.models  # noqa: F401
import app.modules.scoring.models  # noqa: F401
import app.modules.prompt_generation.models  # noqa: F401
import app.modules.approvals.models  # noqa: F401
import app.modules.social_media.models  # noqa: F401

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info("application_starting", app_name=settings.app_name, env=settings.app_env)
    yield
    try:
        from app.modules.ai.providers.http_client import close_ai_http_clients
        await close_ai_http_clients()
    except Exception as e:
        logger.warning("ai_http_client_shutdown_error", error=str(e))
    await close_redis()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Winsta AI Studio API",
        description="Winsta AI Studio for trend intelligence and Social Media AI Agent workflows.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
    )

    # -- CORS --
    allowed_origins = (
        ["*"]
        if settings.is_development
        else [settings.social_frontend_base_url.rstrip("/")]
        if settings.social_frontend_base_url.startswith(("http://", "https://"))
        else []
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        # Production authentication uses bearer tokens; do not advertise
        # credentialed cross-origin requests to arbitrary callers.
        allow_credentials=settings.is_development,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Middleware --
    register_middleware(app)

    # -- Exception Handlers --
    register_exception_handlers(app)

    # -- Health Endpoints --
    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok"}

    @app.get("/health/ready", tags=["Health"])
    async def health_ready():
        """Check critical dependencies: database and Redis."""
        checks: dict = {}

        # Database check
        try:
            from app.core.database import engine
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception:
            logger.exception("health_database_check_failed")
            checks["database"] = "error"

        # Redis check
        try:
            redis = await get_redis()
            await redis.ping()
            checks["redis"] = "ok"
        except Exception:
            logger.exception("health_redis_check_failed")
            checks["redis"] = "error"

        all_ok = all(v == "ok" for v in checks.values())
        return {
            "status": "ready" if all_ok else "degraded",
            "checks": checks,
        }

    # -- Module Routers (API v1) --
    from app.modules.auth.controllers import router as auth_router
    from app.modules.trend_sources.controllers import router as trend_sources_router
    from app.modules.trend_runs.controllers import router as trend_runs_router
    from app.modules.trends.controllers import router as trends_router
    from app.modules.scoring.controllers import router as scoring_router
    from app.modules.prompt_generation.controllers import router as prompt_gen_router
    from app.modules.prompt_generation.controllers.public_router import public_router as public_prompt_router
    from app.modules.approvals.controllers import router as approvals_router
    from app.modules.settings.controllers import router as settings_router
    from app.modules.social_media.controllers import router as social_media_router
    from app.modules.ai.controllers import router as ai_router

    api_v1_prefix = "/api/v1"

    app.include_router(auth_router, prefix=api_v1_prefix)
    app.include_router(trend_sources_router, prefix=api_v1_prefix)
    app.include_router(trend_runs_router, prefix=api_v1_prefix)
    app.include_router(trends_router, prefix=api_v1_prefix)
    app.include_router(scoring_router, prefix=api_v1_prefix)
    app.include_router(prompt_gen_router, prefix=api_v1_prefix)
    app.include_router(public_prompt_router, prefix=api_v1_prefix)
    app.include_router(approvals_router, prefix=api_v1_prefix)
    app.include_router(settings_router, prefix=api_v1_prefix)
    app.include_router(social_media_router, prefix=api_v1_prefix)
    app.include_router(ai_router, prefix=api_v1_prefix)

    return app


app = create_app()
