"""Celery tasks for idempotent downstream delivery."""

import asyncio
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.core.database import get_celery_task_session
from app.modules.integrations.contracts import IntegrationPayload
from app.modules.integrations.enums import DeliveryStatus
from app.modules.integrations.models import IntegrationDelivery
from app.modules.integrations.sarah.adapter import SarahAgentAdapter
from app.modules.integrations.social_media.adapter import SocialMediaAgentAdapter
from app.modules.prompt_generation.models import PromptPackage
from app.modules.trends.enums import TrendStatus
from app.modules.trends.models import Trend
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="app.workers.integration_tasks.deliver_approved_trend",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def deliver_approved_trend(self, trend_id: str) -> dict:
    """Deliver an approved trend once per configured downstream adapter."""
    logger.info("integration_delivery_started", trend_id=trend_id)

    async def execute():
        async with get_celery_task_session() as session:
            trend_uuid = uuid.UUID(trend_id)
            trend = (
                await session.execute(
                    select(Trend).where(Trend.id == trend_uuid, Trend.deleted_at.is_(None))
                )
            ).scalar_one_or_none()
            if not trend:
                return {"trend_id": trend_id, "status": "not_found"}
            if trend.status != TrendStatus.APPROVED.value:
                return {"trend_id": trend_id, "status": "not_approved"}

            package = (
                await session.execute(
                    select(PromptPackage)
                    .where(PromptPackage.trend_id == trend_uuid, PromptPackage.deleted_at.is_(None))
                    .order_by(PromptPackage.version.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            payload = IntegrationPayload(
                trend_id=trend_id,
                prompt_package_id=str(package.id) if package else None,
                score=trend.overall_score,
                approved_at=datetime.now(timezone.utc).isoformat(),
                data={
                    "title": trend.title,
                    "description": trend.description,
                    "category": trend.category,
                    "risk_level": trend.risk_level,
                    "prompt_version": package.version if package else None,
                    "prompts": {
                        "text_to_image": package.text_to_image_prompt,
                        "text_to_video": package.text_to_video_prompt,
                        "text_to_voice": package.text_to_voice_prompt,
                        "image_to_image": package.image_to_image_prompt,
                        "image_to_video": package.image_to_video_prompt,
                        "video_to_video": package.video_to_video_prompt,
                        "negative_prompt": package.negative_prompt,
                    } if package else None,
                },
            )

            results = []
            failed = []
            for adapter in (SarahAgentAdapter(), SocialMediaAgentAdapter()):
                if not await adapter.is_configured():
                    results.append({"integration": adapter.integration_name, "status": "not_configured"})
                    continue
                delivery = (
                    await session.execute(
                        select(IntegrationDelivery)
                        .where(
                            IntegrationDelivery.trend_id == trend_uuid,
                            IntegrationDelivery.integration_type == adapter.integration_name,
                            IntegrationDelivery.deleted_at.is_(None),
                        )
                        .order_by(IntegrationDelivery.created_at.desc())
                        .limit(1)
                    )
                ).scalar_one_or_none()
                if delivery and delivery.status == DeliveryStatus.DELIVERED.value:
                    results.append({"integration": adapter.integration_name, "status": "already_delivered"})
                    continue
                if not delivery:
                    delivery = IntegrationDelivery(
                        trend_id=trend_uuid,
                        prompt_package_id=package.id if package else None,
                        integration_type=adapter.integration_name,
                        status=DeliveryStatus.PENDING.value,
                        payload=payload.data,
                    )
                    session.add(delivery)
                    await session.flush()

                delivery.status = DeliveryStatus.RETRYING.value
                delivery.attempt_count += 1
                result = await adapter.deliver(payload)
                delivery.response_payload = result.response_body
                delivery.error = result.error
                delivery.status = (
                    DeliveryStatus.DELIVERED.value if result.success else DeliveryStatus.FAILED.value
                )
                results.append({
                    "integration": adapter.integration_name,
                    "status": delivery.status,
                    "attempt": delivery.attempt_count,
                })
                if not result.success and delivery.attempt_count < delivery.max_retries:
                    failed.append(f"{adapter.integration_name}: {result.error}")
            await session.commit()
            if failed:
                raise RuntimeError("; ".join(failed))
            return {"trend_id": trend_id, "status": "delivery_completed", "results": results}

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=min(600, 60 * (2 ** self.request.retries)))


@celery_app.task(name="app.workers.integration_tasks.retry_failed_deliveries")
def retry_failed_deliveries() -> dict:
    """Redispatch retryable failed deliveries without duplicating successes."""
    logger.info("retry_failed_deliveries_started")

    async def find_retryable():
        async with get_celery_task_session() as session:
            rows = (
                await session.execute(
                    select(IntegrationDelivery).where(
                        IntegrationDelivery.status == DeliveryStatus.FAILED.value,
                        IntegrationDelivery.attempt_count < IntegrationDelivery.max_retries,
                        IntegrationDelivery.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            return sorted({str(row.trend_id) for row in rows})

    trend_ids = asyncio.run(find_retryable())
    for trend_id in trend_ids:
        deliver_approved_trend.delay(trend_id)
    return {"status": "retry_check_completed", "redispatched": len(trend_ids)}
