"""Sub-service managing Social Publish Jobs, Scheduling, and Queue Operations."""

from datetime import datetime, timezone
import uuid

import structlog

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.modules.social_media.enums import ContentItemStatus, PublishJobStatus
from app.modules.social_media.models import PublishJob
from app.modules.social_media.repositories import SocialContentRepository, SocialPublishJobRepository
from app.modules.social_media.schemas import (
    PublishJobResponse,
    ReschedulePublishJobRequest,
    ScheduleContentRequest,
    SocialPublishQueueItemResponse,
)

logger = structlog.get_logger()


class SocialPublishingService:
    """Encapsulates content scheduling, publish job queue management, and retry handling."""

    def __init__(
        self,
        content_repo: SocialContentRepository,
        publish_job_repo: SocialPublishJobRepository,
    ) -> None:
        self.content_repo = content_repo
        self.publish_job_repo = publish_job_repo

    async def list_publish_jobs(
        self,
        organization_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> dict:
        if status:
            try:
                PublishJobStatus(status)
            except ValueError as exc:
                raise BadRequestException(message=f"Unknown publish job status '{status}'") from exc
        result = await self.publish_job_repo.paginate_queue(
            page=page,
            page_size=page_size,
            status=status,
            organization_id=organization_id,
        )
        result["items"] = [
            SocialPublishQueueItemResponse(
                id=job.id,
                content_variant_id=job.content_variant_id,
                content_item_id=job.content_variant.content_item_id,
                brief_title=job.content_variant.content_item.brief.title,
                platform=job.platform,
                caption=job.content_variant.caption,
                hook=job.content_variant.hook,
                scheduled_at=job.scheduled_at,
                timezone=job.timezone,
                status=job.status,
                idempotency_key=job.idempotency_key,
                attempt_count=job.attempt_count,
                max_attempts=job.max_attempts,
                next_attempt_at=job.next_attempt_at,
                last_attempt_at=job.last_attempt_at,
                error=job.error,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
            for job in result["items"]
        ]
        return result

    async def schedule_content(
        self,
        organization_id: uuid.UUID,
        content_id: uuid.UUID,
        data: ScheduleContentRequest,
    ) -> list[PublishJobResponse]:
        item = await self.content_repo.get_by_id(content_id)
        if not item or item.organization_id != organization_id:
            raise NotFoundException(message="Social content item not found")
        variants = list(item.variants)
        all_variant_ids = {variant.id for variant in variants}
        if data.variant_ids:
            selected_ids = set(data.variant_ids)
            unknown_ids = selected_ids - all_variant_ids
            if unknown_ids:
                raise BadRequestException(message="One or more variants do not belong to this content item")
            variants = [variant for variant in variants if variant.id in selected_ids]
            unapproved = [variant for variant in variants if variant.status != ContentItemStatus.APPROVED.value]
            if unapproved:
                raise BadRequestException(message="Only approved variants can be scheduled")
        else:
            variants = [variant for variant in variants if variant.status == ContentItemStatus.APPROVED.value]
        if not variants:
            raise BadRequestException(message="No approved content variants available for scheduling")

        jobs: list[PublishJobResponse] = []
        now = datetime.now(timezone.utc)
        scheduled_at = data.scheduled_at.astimezone(timezone.utc) if data.scheduled_at else None
        publish_now = scheduled_at is None or scheduled_at <= now
        for variant in variants:
            idempotency_key = f"social:{variant.id}:v{variant.version}:{scheduled_at.isoformat() if scheduled_at else 'now'}"
            existing = await self.publish_job_repo.get_all(
                filters=[PublishJob.idempotency_key == idempotency_key],
                limit=1,
            )
            if existing:
                raise ConflictException(message=f"Publish job already exists for variant {variant.id}")

            job = await self.publish_job_repo.create({
                "organization_id": item.organization_id,
                "content_variant_id": variant.id,
                "platform": variant.platform,
                "scheduled_at": scheduled_at,
                "timezone": data.timezone,
                "status": PublishJobStatus.QUEUED.value if publish_now else PublishJobStatus.SCHEDULED.value,
                "idempotency_key": idempotency_key,
                "next_attempt_at": scheduled_at if not publish_now else None,
            })
            variant.status = ContentItemStatus.SCHEDULED.value
            jobs.append(PublishJobResponse.model_validate(job))

        scheduled_or_published = {
            ContentItemStatus.SCHEDULED.value,
            ContentItemStatus.PUBLISHED.value,
        }
        if {variant.status for variant in item.variants} <= scheduled_or_published:
            item.status = ContentItemStatus.SCHEDULED.value
        await self.content_repo.session.flush()

        if publish_now:
            try:
                from app.workers.social_tasks import publish_social_job
                for job in jobs:
                    publish_social_job.delay(str(job.id))
            except Exception as exc:
                logger.warning("social_publish_dispatch_failed", content_id=str(content_id), error=str(exc))
        else:
            try:
                from app.workers.social_tasks import publish_social_job
                for job in jobs:
                    publish_social_job.apply_async(args=[str(job.id)], eta=scheduled_at)
            except Exception as exc:
                logger.warning("social_publish_schedule_dispatch_failed", content_id=str(content_id), error=str(exc))

        return jobs

    async def cancel_publish_job(self, organization_id: uuid.UUID, job_id: uuid.UUID) -> PublishJobResponse:
        job = await self.publish_job_repo.get_by_id(job_id)
        if not job or job.organization_id != organization_id:
            raise NotFoundException(message="Social publish job not found")
        if job.status in {PublishJobStatus.PUBLISHED.value, PublishJobStatus.PUBLISHING.value}:
            raise ConflictException(message=f"A job in '{job.status}' status cannot be cancelled")
        job.status = PublishJobStatus.CANCELLED.value
        job.next_attempt_at = None
        job.error = None
        if job.content_variant.status == ContentItemStatus.SCHEDULED.value:
            job.content_variant.status = ContentItemStatus.APPROVED.value
        await self.content_repo.session.flush()
        return PublishJobResponse.model_validate(job)

    async def retry_publish_job(self, organization_id: uuid.UUID, job_id: uuid.UUID) -> PublishJobResponse:
        job = await self.publish_job_repo.get_by_id(job_id)
        if not job or job.organization_id != organization_id:
            raise NotFoundException(message="Social publish job not found")
        retryable = {
            PublishJobStatus.FAILED.value,
            PublishJobStatus.CONNECTION_REQUIRED.value,
            PublishJobStatus.MEDIA_REQUIRED.value,
            PublishJobStatus.CANCELLED.value,
        }
        if job.status == PublishJobStatus.SCHEDULED.value and job.error:
            retryable.add(PublishJobStatus.SCHEDULED.value)
        if job.status not in retryable:
            raise ConflictException(message=f"A job in '{job.status}' status cannot be retried")
        job.status = PublishJobStatus.QUEUED.value
        job.attempt_count = 0
        job.next_attempt_at = None
        job.error = None
        if job.scheduled_at and job.scheduled_at <= datetime.now(timezone.utc):
            job.scheduled_at = None
        await self.content_repo.session.flush()
        await self.content_repo.session.commit()
        try:
            from app.workers.social_tasks import publish_social_job
            publish_social_job.delay(str(job.id))
        except Exception as exc:
            logger.warning("social_publish_retry_dispatch_failed", job_id=str(job.id), error=str(exc))
        return PublishJobResponse.model_validate(job)

    async def reschedule_publish_job(
        self,
        organization_id: uuid.UUID,
        job_id: uuid.UUID,
        data: ReschedulePublishJobRequest,
    ) -> PublishJobResponse:
        job = await self.publish_job_repo.get_by_id(job_id)
        if not job or job.organization_id != organization_id:
            raise NotFoundException(message="Social publish job not found")
        if job.status in {PublishJobStatus.PUBLISHED.value, PublishJobStatus.PUBLISHING.value}:
            raise ConflictException(message=f"A job in '{job.status}' status cannot be rescheduled")
        scheduled_at = data.scheduled_at.astimezone(timezone.utc)
        job.scheduled_at = scheduled_at
        job.next_attempt_at = scheduled_at
        job.timezone = data.timezone
        job.status = PublishJobStatus.SCHEDULED.value
        job.attempt_count = 0
        job.error = None
        job.idempotency_key = f"social:{job.content_variant_id}:v{job.content_variant.version}:{scheduled_at.isoformat()}:{job.id}"
        job.content_variant.status = ContentItemStatus.SCHEDULED.value
        await self.content_repo.session.flush()
        return PublishJobResponse.model_validate(job)

