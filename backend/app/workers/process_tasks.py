"""Celery tasks for independently replayable trend-processing stages."""

import asyncio
import uuid

import structlog
from sqlalchemy import select

from app.collectors.base import TrendCandidateData
from app.core.database import get_celery_task_session
from app.modules.scoring.enums import SignalType
from app.modules.scoring.models import ScoringConfiguration, TrendSignal
from app.modules.scoring.services import ScoringService
from app.modules.trend_candidates.enums import CandidateStatus
from app.modules.trend_candidates.models import TrendCandidate
from app.modules.trends.enums import TrendStatus
from app.modules.trends.models import Trend
from app.pipeline.deduplicator import DeduplicationService
from app.pipeline.enricher import EnricherService
from app.pipeline.normalizer import NormalizerService
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(
    name="app.workers.process_tasks.normalize_candidates",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
)
def normalize_candidates(self, trend_run_id: str) -> dict:
    """Normalize raw candidates from a trend run."""
    logger.info("normalize_started", trend_run_id=trend_run_id)
    async def execute():
        async with get_celery_task_session() as session:
            candidates = (
                await session.execute(
                    select(TrendCandidate).where(
                        TrendCandidate.trend_run_id == uuid.UUID(trend_run_id),
                        TrendCandidate.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            service = NormalizerService()
            for candidate in candidates:
                normalized = service.normalize(_to_candidate_data(candidate))
                candidate.title = normalized.title
                candidate.caption = normalized.caption
                candidate.hashtags = normalized.hashtags
                candidate.engagement_rate = normalized.engagement_rate
                candidate.status = CandidateStatus.NORMALIZED.value
            await session.commit()
            return {"trend_run_id": trend_run_id, "stage": "normalized", "count": len(candidates)}

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.process_tasks.deduplicate_candidates",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
)
def deduplicate_candidates(self, trend_run_id: str) -> dict:
    """Deduplicate candidates using DeduplicationService."""
    logger.info("deduplication_started", trend_run_id=trend_run_id)
    async def execute():
        async with get_celery_task_session() as session:
            run_uuid = uuid.UUID(trend_run_id)
            current = (
                await session.execute(
                    select(TrendCandidate).where(
                        TrendCandidate.trend_run_id == run_uuid,
                        TrendCandidate.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            prior = (
                await session.execute(
                    select(TrendCandidate).where(
                        TrendCandidate.trend_run_id != run_uuid,
                        TrendCandidate.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            service = DeduplicationService()
            external_ids = {c.external_id for c in prior if c.external_id}
            urls = {c.canonical_url for c in prior if c.canonical_url}
            hashes = {c.content_hash for c in prior if c.content_hash}
            titles = [c.title for c in prior if c.title]
            hashtag_sets = [set(c.hashtags or []) for c in prior if c.hashtags]
            duplicates = 0
            for candidate in current:
                content_hash = service.compute_content_hash(candidate.title or "", candidate.caption or "")
                duplicate, reason = service.check_all(
                    external_id=candidate.external_id,
                    canonical_url=candidate.canonical_url,
                    title=candidate.title,
                    content_hash=content_hash,
                    hashtags=candidate.hashtags,
                    existing_external_ids=external_ids,
                    existing_urls=urls,
                    existing_hashes=hashes,
                    existing_titles=titles,
                    existing_hashtag_sets=hashtag_sets,
                )
                candidate.content_hash = content_hash
                candidate.status = CandidateStatus.DUPLICATE.value if duplicate else CandidateStatus.DEDUPLICATED.value
                payload = dict(candidate.raw_payload or {})
                payload["deduplication_reason"] = reason
                candidate.raw_payload = payload
                duplicates += int(duplicate)
                if candidate.external_id:
                    external_ids.add(candidate.external_id)
                if candidate.canonical_url:
                    urls.add(candidate.canonical_url)
                hashes.add(content_hash)
                if candidate.title:
                    titles.append(candidate.title)
                if candidate.hashtags:
                    hashtag_sets.append(set(candidate.hashtags))
            await session.commit()
            return {
                "trend_run_id": trend_run_id,
                "stage": "deduplicated",
                "count": len(current),
                "duplicates": duplicates,
            }

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.process_tasks.enrich_candidates",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
)
def enrich_candidates(self, trend_run_id: str) -> dict:
    """Enrich candidates with additional metadata."""
    logger.info("enrichment_started", trend_run_id=trend_run_id)
    async def execute():
        async with get_celery_task_session() as session:
            candidates = (
                await session.execute(
                    select(TrendCandidate).where(
                        TrendCandidate.trend_run_id == uuid.UUID(trend_run_id),
                        TrendCandidate.status == CandidateStatus.DEDUPLICATED.value,
                        TrendCandidate.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            service = EnricherService()
            for candidate in candidates:
                enriched = service.enrich({
                    "title": candidate.title,
                    "caption": candidate.caption,
                    "hashtags": candidate.hashtags,
                    "language": candidate.language,
                    "raw_payload": candidate.raw_payload,
                })
                for field in ("title", "caption", "hashtags", "language", "raw_payload"):
                    if field in enriched:
                        setattr(candidate, field, enriched[field])
                candidate.status = CandidateStatus.ENRICHED.value
            await session.commit()
            return {"trend_run_id": trend_run_id, "stage": "enriched", "count": len(candidates)}

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(
    name="app.workers.process_tasks.calculate_scores",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
)
def calculate_scores(self, trend_id: str) -> dict:
    """Calculate deterministic scoring signals for a trend."""
    logger.info("scoring_started", trend_id=trend_id)
    async def execute():
        async with get_celery_task_session() as session:
            trend_uuid = uuid.UUID(trend_id)
            trend = (
                await session.execute(
                    select(Trend).where(Trend.id == trend_uuid, Trend.deleted_at.is_(None))
                )
            ).scalar_one_or_none()
            if not trend:
                return {"trend_id": trend_id, "stage": "not_found"}
            signals_rows = (
                await session.execute(
                    select(TrendSignal).where(
                        TrendSignal.trend_id == trend_uuid,
                        TrendSignal.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            config_rows = (
                await session.execute(
                    select(ScoringConfiguration).where(
                        ScoringConfiguration.is_active.is_(True),
                        ScoringConfiguration.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            signals = {row.signal_type: row.normalized_value for row in signals_rows}
            weights = (
                {row.signal_type: row.weight for row in config_rows}
                if config_rows
                else {signal.value: weight for signal, weight in SignalType.default_weights().items()}
            )
            score = ScoringService(config_repo=None, signal_repo=None).calculate_score(signals, weights)
            trend.overall_score = score
            trend.status = TrendStatus.SCORED.value
            await session.commit()
            return {"trend_id": trend_id, "stage": "scored", "score": score}

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


def _to_candidate_data(candidate: TrendCandidate) -> TrendCandidateData:
    return TrendCandidateData(
        platform=candidate.platform,
        external_id=candidate.external_id,
        canonical_url=candidate.canonical_url,
        title=candidate.title,
        caption=candidate.caption,
        hashtags=candidate.hashtags,
        author_name=candidate.author_name,
        published_at=candidate.published_at,
        view_count=candidate.view_count,
        like_count=candidate.like_count,
        comment_count=candidate.comment_count,
        share_count=candidate.share_count,
        engagement_rate=candidate.engagement_rate,
        media_type=candidate.media_type,
        thumbnail_url=candidate.thumbnail_url,
        raw_payload=candidate.raw_payload,
        language=candidate.language,
    )
