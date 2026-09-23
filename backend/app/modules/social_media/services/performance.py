"""Closed-loop performance analysis for social content.

The analyzer is deterministic so recommendations stay reproducible and useful
even when no LLM provider is available. An AI explanation layer can be added on
top later without changing the persisted evidence contract.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.social_media.models import (
    ContentVariant,
    PublishJob,
    SocialMetricSnapshot,
    SocialPerformanceInsight,
)


VIEW_KEYS = (
    "views",
    "view_count",
    "viewCount",
    "impressions",
    "impression_count",
    "post_impressions",
    "reach",
    "plays",
    "play_count",
)
ENGAGEMENT_TOTAL_KEYS = ("engagements", "engagement_count", "post_engaged_users")
ENGAGEMENT_KEY_GROUPS = (
    ("likes", "like_count", "likeCount"),
    ("reactions", "post_reactions_by_type_total"),
    ("comments", "comment_count", "commentCount"),
    ("shares", "share_count", "shareCount", "retweet_count"),
    ("saves", "saved", "bookmark_count"),
    ("clicks", "url_link_clicks"),
)


@dataclass(frozen=True)
class PerformanceSample:
    publish_job_id: uuid.UUID
    platform: str
    language: str | None
    content_format: str | None
    metrics: dict[str, Any]


@dataclass(frozen=True)
class CalculatedInsight:
    platform: str | None
    language: str | None
    content_format: str | None
    sample_size: int
    performance_score: float
    engagement_rate: float
    confidence: float
    summary: str
    recommendations: list[dict[str, Any]]
    evidence: dict[str, Any]


def _number(value: Any) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return max(0.0, float(value))
    if isinstance(value, dict):
        return sum(_number(item) for item in value.values())
    if isinstance(value, str):
        try:
            return max(0.0, float(value.replace(",", "")))
        except ValueError:
            return 0.0
    return 0.0


def _first_metric(metrics: dict[str, Any], keys: tuple[str, ...]) -> float:
    for key in keys:
        value = _number(metrics.get(key))
        if value:
            return value
    return 0.0


def _sample_totals(sample: PerformanceSample) -> tuple[float, float, float]:
    views = _first_metric(sample.metrics, VIEW_KEYS)
    engagements = _first_metric(sample.metrics, ENGAGEMENT_TOTAL_KEYS)
    if engagements == 0:
        engagements = sum(
            _first_metric(sample.metrics, aliases)
            for aliases in ENGAGEMENT_KEY_GROUPS
        )
    rate = engagements / views * 100 if views else 0.0
    score = min(100.0, rate * 8 + min(20.0, math.log10(views + 1) * 5))
    return views, engagements, score


def calculate_performance_insights(samples: list[PerformanceSample]) -> list[CalculatedInsight]:
    """Aggregate latest-per-post samples into overall and targetable segments."""
    if not samples:
        return []

    groups: dict[tuple[str | None, str | None, str | None], list[PerformanceSample]] = {
        (None, None, None): samples
    }
    for sample in samples:
        groups.setdefault((sample.platform, sample.language, sample.content_format), []).append(sample)

    calculated: list[CalculatedInsight] = []
    for (platform, language, content_format), group in groups.items():
        totals = [_sample_totals(sample) for sample in group]
        views = sum(item[0] for item in totals)
        engagements = sum(item[1] for item in totals)
        engagement_rate = engagements / views * 100 if views else 0.0
        score = sum(item[2] for item in totals) / len(totals)
        confidence = min(1.0, len(group) / 10)
        best_index = max(range(len(group)), key=lambda index: totals[index][2])
        best = group[best_index]

        segment = "all published content"
        if platform:
            segment = " / ".join(part for part in (platform, language, content_format) if part)
        if len(group) < 3:
            summary = f"{segment}: early signal from {len(group)} post(s); collect more data before automation."
            action = "collect_more_data"
            hypothesis = "At least three comparable posts will produce a more reliable baseline."
        elif engagement_rate < 1:
            summary = f"{segment}: engagement is below 1%; prioritize a stronger opening hook and clearer CTA."
            action = "test_hook_and_cta"
            hypothesis = "A benefit-led first sentence and one explicit CTA will improve engagement rate."
        else:
            summary = f"{segment}: engagement baseline is {engagement_rate:.2f}%; preserve the winner and test one challenger."
            action = "create_controlled_challenger"
            hypothesis = "Changing only the hook will reveal whether the winning pattern is repeatable."

        calculated.append(CalculatedInsight(
            platform=platform,
            language=language,
            content_format=content_format,
            sample_size=len(group),
            performance_score=round(score, 2),
            engagement_rate=round(engagement_rate, 4),
            confidence=round(confidence, 2),
            summary=summary,
            recommendations=[{
                "action": action,
                "priority": "high" if platform is None else "medium",
                "experiment": {
                    "variable": "hook",
                    "control_publish_job_id": str(best.publish_job_id),
                    "hypothesis": hypothesis,
                    "approval_required": True,
                },
            }],
            evidence={
                "total_views": round(views),
                "total_engagements": round(engagements),
                "latest_post_ids": [str(sample.publish_job_id) for sample in group[:10]],
                "metric_formula": "engagements / views * 100",
            },
        ))
    return sorted(calculated, key=lambda item: (item.platform is not None, -item.performance_score))


async def refresh_performance_insights(
    session: AsyncSession,
    organization_id: uuid.UUID,
) -> list[SocialPerformanceInsight]:
    """Refresh materialized insights using only the newest snapshot per publish job."""
    result = await session.execute(
        select(SocialMetricSnapshot, PublishJob, ContentVariant)
        .join(PublishJob, PublishJob.id == SocialMetricSnapshot.publish_job_id)
        .join(ContentVariant, ContentVariant.id == PublishJob.content_variant_id)
        .where(SocialMetricSnapshot.organization_id == organization_id)
        .where(SocialMetricSnapshot.deleted_at.is_(None))
        .where(PublishJob.deleted_at.is_(None))
        .where(ContentVariant.deleted_at.is_(None))
        .order_by(SocialMetricSnapshot.captured_at.desc())
        .limit(1000)
    )
    samples: list[PerformanceSample] = []
    seen_jobs: set[uuid.UUID] = set()
    for snapshot, job, variant in result.all():
        if job.id in seen_jobs:
            continue
        seen_jobs.add(job.id)
        samples.append(PerformanceSample(
            publish_job_id=job.id,
            platform=job.platform,
            language=variant.language,
            content_format=variant.format,
            metrics=snapshot.metrics or {},
        ))

    calculated = calculate_performance_insights(samples)
    if not calculated:
        return []

    existing_result = await session.execute(
        select(SocialPerformanceInsight)
        .where(SocialPerformanceInsight.organization_id == organization_id)
        .where(SocialPerformanceInsight.status == "active")
        .where(SocialPerformanceInsight.deleted_at.is_(None))
    )
    existing = {
        (item.platform, item.language, item.content_format): item
        for item in existing_result.scalars().all()
    }
    now = datetime.now(timezone.utc)
    refreshed: list[SocialPerformanceInsight] = []
    active_keys = set()
    for item in calculated:
        key = (item.platform, item.language, item.content_format)
        active_keys.add(key)
        record = existing.get(key)
        if record is None:
            record = SocialPerformanceInsight(organization_id=organization_id)
            session.add(record)
        record.platform = item.platform
        record.language = item.language
        record.content_format = item.content_format
        record.sample_size = item.sample_size
        record.performance_score = item.performance_score
        record.engagement_rate = item.engagement_rate
        record.confidence = item.confidence
        record.summary = item.summary
        record.recommendations = item.recommendations
        record.evidence = item.evidence
        record.status = "active"
        record.analyzed_at = now
        refreshed.append(record)

    for key, record in existing.items():
        if key not in active_keys:
            record.status = "superseded"
    await session.flush()
    return refreshed
