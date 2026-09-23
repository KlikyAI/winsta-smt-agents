"""Celery application configuration with separate task queues."""

from celery import Celery

from app.core.config import get_settings
from app.workers.beat_schedule import get_beat_schedule

# Import all SQLAlchemy models so relationships and mappers are registered in Celery workers
import app.modules.auth.models  # noqa: F401
import app.modules.trend_sources.models  # noqa: F401
import app.modules.trend_runs.models  # noqa: F401
import app.modules.trend_candidates.models  # noqa: F401
import app.modules.trends.models  # noqa: F401
import app.modules.scoring.models  # noqa: F401
import app.modules.prompt_generation.models  # noqa: F401
import app.modules.approvals.models  # noqa: F401
import app.modules.social_media.models  # noqa: F401

settings = get_settings()

celery_app = Celery(
    "prompt_trends",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.workers.collect_tasks",
        "app.workers.process_tasks",
        "app.workers.ai_tasks",
        "app.workers.integration_tasks",
        "app.workers.social_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # Task routing to separate queues
    task_routes={
        "app.workers.collect_tasks.*": {"queue": "trend.collect"},
        "app.workers.process_tasks.*": {"queue": "trend.process"},
        "app.workers.ai_tasks.*": {"queue": "trend.ai"},
        "app.workers.integration_tasks.*": {"queue": "trend.integration"},
        "app.workers.social_tasks.generate_social_content": {"queue": "social.generate"},
        "app.workers.social_tasks.publish_social_job": {"queue": "social.publish"},
        "app.workers.social_tasks.dispatch_due_social_jobs": {"queue": "social.publish"},
        "app.workers.social_tasks.refresh_expiring_social_tokens": {"queue": "social.publish"},
        "app.workers.social_tasks.sync_social_analytics": {"queue": "social.analytics"},
    },

    # Default queue
    task_default_queue="trend.process",

    # Register periodic workflows, including the one-minute social publish dispatcher.
    beat_schedule=get_beat_schedule(),
)

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.workers",
])
