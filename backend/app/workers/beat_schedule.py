"""Celery Beat schedule configuration.

Scheduled tasks are configurable via environment variables.
Default schedules provided for development.
"""

from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()


def get_beat_schedule() -> dict:
    """Build Celery Beat schedule from configuration."""
    interval_minutes = settings.discovery_schedule_minutes

    schedule = {
        "retry-failed-integrations": {
            "task": "app.workers.integration_tasks.retry_failed_deliveries",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "trend.integration"},
        },
        "sync-social-analytics": {
            "task": "app.workers.social_tasks.sync_social_analytics",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "social.analytics"},
        },
        "refresh-expiring-social-tokens": {
            "task": "app.workers.social_tasks.refresh_expiring_social_tokens",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "social.publish"},
        },
        "dispatch-due-social-jobs": {
            "task": "app.workers.social_tasks.dispatch_due_social_jobs",
            "schedule": crontab(minute="*"),
            "options": {"queue": "social.publish"},
        },
    }
    if settings.discovery_schedule_enabled:
        schedule["scheduled-trend-discovery"] = {
            "task": "app.workers.collect_tasks.scheduled_discovery",
            "schedule": crontab(minute=f"*/{interval_minutes}"),
            "options": {"queue": "trend.collect"},
        }
    return schedule
