"""Celery tasks for trend collection and end-to-end trend synthesis."""

import asyncio
import concurrent.futures
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select

from app.collectors.base import TrendCollectionRequest
from app.collectors.registry import get_collector
from app.core.database import get_celery_task_session
from app.modules.trend_candidates.models import TrendCandidate
from app.modules.trend_runs.models import TrendRun
from app.modules.trends.models import Trend, TrendEvidence
from app.modules.scoring.models import TrendSignal
from app.modules.prompt_generation.models import PromptPackage
from app.modules.ai.agents.trend_workflow import TrendAutomationWorkflow
from app.modules.scoring.enums import SignalType
from app.modules.scoring.models import ScoringConfiguration
from app.modules.trend_candidates.enums import CandidateStatus
from app.modules.trends.enums import TrendStatus
from app.modules.trend_runs.enums import TrendRunStatus
from app.workers.celery_app import celery_app

logger = structlog.get_logger()

import json
from app.modules.ai.services.service import ai_service
from app.core.config import get_settings

AESTHETIC_STYLES = {
    "minimalist_organic": "minimalist organic aesthetic, raw limestone texture, soft warm sunlight, linen drape, earth tones, clean composition, trending on Behance",
    "cyberpunk_neon": "cyberpunk neo-noir aesthetic, glowing cyan and magenta neon signs, wet asphalt reflections, volumetric atmosphere, anamorphic lens flare",
    "luxury_editorial": "luxury high-fashion editorial aesthetic, liquid chrome accents, dramatic studio backlight, 8k commercial grading, glossy reflections",
    "vintage_retro": "retro 90s aesthetic, analog VHS camcorder texture, subtle chromatic aberration, 35mm film grain, nostalgic warm color grade",
    "warm_cinematic": "cinematic golden hour lighting, rich warm shadows, atmospheric dust particles, natural depth of field, 35mm prime shot",
    "bold_vibrant": "bold vibrant pop art aesthetic, high saturation color harmony, dynamic punchy contrast, modern studio key visual",
}


def generate_6_modality_prompts(
    title: str,
    caption: str,
    tags: list[str],
    aesthetic: str = "minimalist_organic",
    category: str = "general",
) -> dict:
    """Synthesize complete 6-modality prompt package tailored to chosen aesthetic and category."""
    style_desc = AESTHETIC_STYLES.get(aesthetic, AESTHETIC_STYLES["minimalist_organic"])
    tag_str = ", ".join(tags) if tags else "cinematic, viral"
    category_label = category.replace("_", " ").title()

    return {
        "text_to_image": (
            f"Hyper-detailed photorealistic commercial key visual of {title}. "
            f"Style: {style_desc}. 8k resolution, shot on Hasselblad H6D-100c, 35mm prime lens, "
            f"clean commercial grading. Concept: {caption[:120]}. Keywords: {tag_str}."
        ),
        "text_to_video": (
            f"Cinematic slow-motion 60fps tracking camera shot capturing {title}. "
            f"Style mood: {style_desc}. Dynamic movement, natural physics, soft depth of field, "
            f"ultra-high production value, 4k master. Action: {caption[:140]}."
        ),
        "text_to_voice": (
            f"[Tone: Inspiring, Authoritative, Contemporary Voiceover]\n"
            f"\"In a world shaped by {category_label}, {title} sets a new benchmark. "
            f"{caption[:100]}... Experience the future of creativity where visual storytelling meets innovation.\""
        ),
        "image_to_image": (
            f"ControlNet Depth & Canny style transfer: Transform base image with {style_desc}. "
            f"Preserve key geometry of {title} while replacing materials with premium styling and studio lighting."
        ),
        "image_to_video": (
            f"Motion brush applied to focal elements: Smooth continuous orbital camera pan with {style_desc}. "
            f"Bring static composition of {title} to life with fluid atmospheric particles and gentle camera push-in."
        ),
        "video_to_video": (
            f"Neural stylization: Re-render source video in {style_desc}. "
            f"Enhance visual fidelity and aesthetic consistency inspired by {title}. Consistency factor: 0.88."
        ),
        "negative_prompt": "blurry, low quality, distorted anatomy, text artifacts, watermark, oversaturated, bad composition, noisy",
        "provider": "deterministic",
        "model": "template-engine",
    }


async def generate_6_modality_prompts_async(
    title: str,
    caption: str,
    tags: list[str],
    aesthetic: str = "minimalist_organic",
    category: str = "general",
    validation_feedback: list[str] | None = None,
) -> tuple[dict, str, str]:
    """Generate 6-modality prompts using active LLM provider (OpenAI, Claude, Gemini, DeepSeek, Groq, Ollama), with fallback."""
    style_desc = AESTHETIC_STYLES.get(aesthetic, AESTHETIC_STYLES["minimalist_organic"])
    tag_str = ", ".join(tags) if tags else "cinematic, viral"

    system_prompt = (
        "You are an expert AI prompt engineer for creative studio production. "
        "Generate 6 specialized AI prompts for commercial creative workflows (Midjourney, Sora, Runway, ElevenLabs, Kling). "
        "Return ONLY a valid JSON object with the keys: text_to_image, text_to_video, text_to_voice, image_to_image, image_to_video, video_to_video, negative_prompt."
    )
    user_prompt = (
        f"Create a production prompt package for trend: '{title}'\n"
        f"Category: {category}\n"
        f"Aesthetic Vibe: {aesthetic} ({style_desc})\n"
        f"Context / Caption: {caption}\n"
        f"Keywords: {tag_str}\n\n"
        "Output structured JSON with complete prompts for each of the 6 modalities."
    )
    if validation_feedback:
        user_prompt += (
            "\n\nThe previous output failed validation. Correct every issue below and return "
            "a complete replacement JSON object:\n- " + "\n- ".join(validation_feedback)
        )

    try:
        resp = await ai_service.generate(
            capability="prompt_generation",
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json",
        )
        content_text = resp.content.strip()
        # Clean any markdown code fences if LLM wrapped in ```json
        if content_text.startswith("```"):
            content_text = content_text.split("\n", 1)[-1]
            if content_text.endswith("```"):
                content_text = content_text.rsplit("```", 1)[0]

        parsed = json.loads(content_text)
        required_keys = ["text_to_image", "text_to_video", "text_to_voice", "image_to_image", "image_to_video", "video_to_video", "negative_prompt"]
        if all(k in parsed for k in required_keys):
            return parsed, resp.provider, resp.model
    except Exception as e:
        logger.warning("llm_prompt_synthesis_fallback", error=str(e))

    # Fallback to deterministic synthesis
    fb = generate_6_modality_prompts(title, caption, tags, aesthetic, category)
    return fb, "deterministic", "template-engine"


@celery_app.task(
    name="app.workers.collect_tasks.run_trend_discovery",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def run_trend_discovery(self, trend_run_id: str) -> dict:
    """Execute trend discovery for a specific run with 4-parameter targeting."""
    logger.info("trend_discovery_started", trend_run_id=trend_run_id)

    async def execute():
        async with get_celery_task_session() as session:
            run_uuid = uuid.UUID(trend_run_id)
            stmt = select(TrendRun).where(TrendRun.id == run_uuid)
            run = (await session.execute(stmt)).scalar_one_or_none()
            if not run:
                logger.error("trend_run_not_found", trend_run_id=trend_run_id)
                return {"error": "not_found"}

            # Idempotent terminal-state guard for duplicate Celery delivery.
            if run.status in {
                TrendRunStatus.COMPLETED.value,
                TrendRunStatus.PARTIALLY_COMPLETED.value,
                TrendRunStatus.CANCELLED.value,
            }:
                return {"trend_run_id": trend_run_id, "status": run.status, "idempotent": True}

            # 1. Update status to running
            run.status = TrendRunStatus.RUNNING.value
            run.started_at = datetime.now(timezone.utc)
            await session.commit()

            # Read run metadata using metadata_ attribute
            run_meta = run.metadata_ or {}
            target_country = run_meta.get("country") or run.market or "ID"
            target_category = run_meta.get("category") or (run.categories[0] if run.categories else "all")
            target_aesthetic = run_meta.get("aesthetic") or "minimalist_organic"
            target_time_window = run_meta.get("time_window") or "24h"

            # 2. Fan out registered platform collectors. AI output is retained as
            # an unverified hypothesis and can never auto-promote to a Trend.
            sources = run.sources or ["google_trends", "tiktok", "instagram", "youtube", "x", "linkedin"]
            platform_errors: dict[str, str] = {}

            from app.modules.ai.agents.discovery_agent import trend_discovery_agent

            async def collect_platform(platform: str):
                collector = get_collector(platform)
                items = []

                if collector:
                    req = TrendCollectionRequest(
                        categories=[target_category] if target_category != "all" else [],
                        market=target_country.lower(),
                        language=run.language or "en",
                        limit=run.limit_per_source or 5,
                    )
                    try:
                        items = await collector.collect(req)
                    except Exception as err:
                        logger.warning("collector_scrape_warning", platform=platform, error=str(err))
                        platform_errors[platform] = str(err)

                has_verified_items = any(
                    (item.raw_payload or {}).get("data_quality") in {"official_api", "official_video"}
                    for item in items
                )
                if not has_verified_items:
                    try:
                        ai_items = await trend_discovery_agent.discover_platform_candidates(
                            platform=platform,
                            category=target_category,
                            market=target_country,
                            language=run.language or "en",
                            aesthetic=target_aesthetic,
                            time_window=target_time_window,
                            limit=min(run.limit_per_source or 3, 4),
                        )
                        if ai_items:
                            items.extend(ai_items)
                    except Exception as err:
                        logger.warning("ai_discovery_error", platform=platform, error=str(err))
                        platform_errors[platform] = str(err)
                return items

            collected_by_platform = await asyncio.gather(
                *(collect_platform(platform) for platform in sources)
            )
            collected_items = [item for items in collected_by_platform for item in items]

            # Respect cancellation requested while collectors were running.
            await session.refresh(run)
            if run.status == TrendRunStatus.CANCELLED.value:
                return {"trend_run_id": trend_run_id, "status": run.status}

            # Load data-driven scoring configuration, falling back to enum defaults.
            config_rows = (
                await session.execute(
                    select(ScoringConfiguration).where(
                        ScoringConfiguration.is_active.is_(True),
                        ScoringConfiguration.deleted_at.is_(None),
                    )
                )
            ).scalars().all()
            weights = (
                {row.signal_type: row.weight for row in config_rows}
                if config_rows
                else {signal.value: weight for signal, weight in SignalType.default_weights().items()}
            )

            # Seed cross-run deduplication context once, then update it after each item.
            prior_candidates = (
                await session.execute(
                    select(TrendCandidate).where(TrendCandidate.deleted_at.is_(None))
                )
            ).scalars().all()
            existing_external_ids = {c.external_id for c in prior_candidates if c.external_id}
            existing_urls = {c.canonical_url for c in prior_candidates if c.canonical_url}
            existing_hashes = {c.content_hash for c in prior_candidates if c.content_hash}
            existing_titles = [c.title for c in prior_candidates if c.title]
            existing_hashtag_sets = [set(c.hashtags or []) for c in prior_candidates if c.hashtags]

            workflow = TrendAutomationWorkflow(generate_6_modality_prompts_async)
            created_candidates: list[TrendCandidate] = []
            promoted_trends_count = 0
            for item in collected_items:
                workflow_state = await workflow.run(
                    item,
                    category=target_category,
                    aesthetic=target_aesthetic,
                    score_threshold=get_settings().scoring_threshold,
                    weights=weights,
                    existing_external_ids=existing_external_ids,
                    existing_urls=existing_urls,
                    existing_hashes=existing_hashes,
                    existing_titles=existing_titles,
                    existing_hashtag_sets=existing_hashtag_sets,
                )
                processed = workflow_state["candidate"]
                workflow_status = workflow_state["status"]
                if workflow_status == "pending_review":
                    candidate_status = CandidateStatus.ACCEPTED.value
                elif workflow_status == "needs_verification":
                    candidate_status = CandidateStatus.NEEDS_VERIFICATION.value
                elif workflow_status == "duplicate":
                    candidate_status = CandidateStatus.DUPLICATE.value
                else:
                    candidate_status = CandidateStatus.REJECTED.value

                payload = dict(processed.get("raw_payload") or {})
                payload["workflow"] = {
                    "status": workflow_status,
                    "duplicate_reason": workflow_state.get("duplicate_reason", ""),
                    "verification_reason": workflow_state.get("verification_reason", ""),
                    "validation_errors": workflow_state.get("validation_errors", []),
                }
                cand = TrendCandidate(
                    trend_run_id=run_uuid,
                    platform=processed.get("platform") or "unknown",
                    status=candidate_status,
                    external_id=processed.get("external_id"),
                    title=processed.get("title"),
                    caption=processed.get("caption"),
                    canonical_url=processed.get("canonical_url"),
                    author_name=processed.get("author_name"),
                    hashtags=processed.get("hashtags") or [],
                    published_at=processed.get("published_at"),
                    engagement_rate=processed.get("engagement_rate"),
                    view_count=processed.get("view_count"),
                    like_count=processed.get("like_count"),
                    comment_count=processed.get("comment_count"),
                    share_count=processed.get("share_count"),
                    media_type=processed.get("media_type"),
                    thumbnail_url=processed.get("thumbnail_url"),
                    content_hash=processed.get("content_hash"),
                    raw_payload=payload,
                    language=processed.get("language"),
                )
                session.add(cand)
                await session.flush()
                created_candidates.append(cand)

                if cand.external_id:
                    existing_external_ids.add(cand.external_id)
                if cand.canonical_url:
                    existing_urls.add(cand.canonical_url)
                if cand.content_hash:
                    existing_hashes.add(cand.content_hash)
                if cand.title:
                    existing_titles.append(cand.title)
                if cand.hashtags:
                    existing_hashtag_sets.append(set(cand.hashtags))

                if workflow_status != "pending_review":
                    continue

                overall_score = workflow_state["overall_score"]
                package = workflow_state["prompt_package"]
                trend = Trend(
                    title=cand.title or "Emerging Visual Trend",
                    description=cand.caption,
                    core_concept=package.get("core_concept") or cand.caption,
                    category=target_category if target_category != "all" else (cand.hashtags[0] if cand.hashtags else "creative"),
                    status=TrendStatus.PENDING_REVIEW.value,
                    overall_score=overall_score,
                    risk_level="high" if workflow_state.get("risk_flags") else "low",
                    first_seen_at=cand.published_at or datetime.now(timezone.utc),
                    last_seen_at=datetime.now(timezone.utc),
                )
                session.add(trend)
                await session.flush()

                session.add(TrendEvidence(
                    trend_id=trend.id,
                    trend_candidate_id=cand.id,
                    platform=cand.platform,
                    relevance_score=overall_score,
                ))
                for signal_type, value in workflow_state["signals"].items():
                    weight = weights.get(signal_type, 0.0)
                    session.add(TrendSignal(
                        trend_id=trend.id,
                        signal_type=signal_type,
                        raw_value=value,
                        normalized_value=value,
                        weight=weight,
                        weighted_score=round(value * (weight / 100.0), 2),
                        source="deterministic",
                    ))

                session.add(PromptPackage(
                    trend_id=trend.id,
                    version=1,
                    trend_title=package["trend_title"],
                    description=package.get("description"),
                    core_concept=package.get("core_concept"),
                    category=trend.category,
                    generation_modes=package.get("generation_modes"),
                    text_to_image_prompt=package.get("text_to_image_prompt"),
                    image_prompt=package.get("image_prompt"),
                    text_to_video_prompt=package.get("text_to_video_prompt"),
                    text_to_voice_prompt=package.get("text_to_voice_prompt"),
                    image_to_image_prompt=package.get("image_to_image_prompt"),
                    image_to_video_prompt=package.get("image_to_video_prompt"),
                    video_to_video_prompt=package.get("video_to_video_prompt"),
                    negative_prompt=package.get("negative_prompt"),
                    tags=package.get("tags"),
                    quality_score=workflow_state["quality_score"],
                    risk_flags=workflow_state.get("risk_flags", []),
                    validation_status="passed",
                    ai_provider=workflow_state.get("prompt_provider"),
                    ai_model=workflow_state.get("prompt_model"),
                    template_version="langgraph-v1",
                    generated_at=datetime.now(timezone.utc),
                ))
                promoted_trends_count += 1

            total_candidates = len(created_candidates)
            accepted = sum(1 for c in created_candidates if c.status == CandidateStatus.ACCEPTED.value)

            # 4. Complete discovery run
            run.candidate_count = total_candidates
            run.accepted_count = accepted
            run.rejected_count = total_candidates - accepted
            run.error_count = len(platform_errors)
            
            # Preserve metadata
            updated_meta = dict(run_meta)
            updated_meta["platform_errors"] = platform_errors
            run.metadata_ = updated_meta
            
            if total_candidates == 0:
                run.status = TrendRunStatus.FAILED.value
            elif platform_errors:
                run.status = TrendRunStatus.PARTIALLY_COMPLETED.value
            else:
                run.status = TrendRunStatus.COMPLETED.value
            run.completed_at = datetime.now(timezone.utc)
            await session.commit()

            logger.info(
                "trend_discovery_completed",
                trend_run_id=trend_run_id,
                country=target_country,
                category=target_category,
                aesthetic=target_aesthetic,
                candidates=total_candidates,
                errors=len(platform_errors),
            )
            return {
                "trend_run_id": trend_run_id,
                "status": run.status,
                "candidate_count": total_candidates,
                "error_count": len(platform_errors),
                "country": target_country,
                "category": target_category,
                "aesthetic": target_aesthetic,
            }

    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, execute()).result()
        else:
            return asyncio.run(execute())
    except Exception as exc:
        logger.error("trend_discovery_failed", trend_run_id=trend_run_id, error=str(exc))

        # Update run status to failed in DB so it does not hang on 'running'
        async def mark_failed():
            try:
                async with get_celery_task_session() as s:
                    st = select(TrendRun).where(TrendRun.id == uuid.UUID(trend_run_id))
                    r = (await s.execute(st)).scalar_one_or_none()
                    if r:
                        r.status = "failed"
                        r.completed_at = datetime.now(timezone.utc)
                        r.error_count = 1
                        m = dict(r.metadata_ or {})
                        m["task_error"] = str(exc)
                        r.metadata_ = m
                        await s.commit()
            except Exception:
                pass

        try:
            asyncio.run(mark_failed())
        except Exception:
            pass

        raise self.retry(exc=exc, countdown=min(300, 30 * (2 ** self.request.retries)))


@celery_app.task(name="app.workers.collect_tasks.scheduled_discovery")
def scheduled_discovery() -> dict:
    """Celery Beat scheduled task for automatic trend discovery."""
    logger.info("scheduled_discovery_triggered")
    
    async def create_scheduled_run():
        async with get_celery_task_session() as session:
            settings = get_settings()
            scheduled_sources = [
                source.strip()
                for source in settings.discovery_schedule_sources.split(",")
                if source.strip()
            ]
            new_run = TrendRun(
                status="queued",
                trigger_type="scheduled",
                market=settings.discovery_schedule_country.lower(),
                sources=scheduled_sources,
                limit_per_source=settings.default_limit_per_source,
                metadata_={
                    "country": settings.discovery_schedule_country.upper(),
                    "category": settings.discovery_schedule_category,
                    "aesthetic": settings.discovery_schedule_aesthetic,
                    "time_window": settings.discovery_schedule_time_window,
                }
            )
            session.add(new_run)
            await session.commit()
            await session.refresh(new_run)
            return str(new_run.id)

    try:
        run_id = asyncio.run(create_scheduled_run())
        run_trend_discovery.delay(run_id)
        return {"trend_run_id": run_id, "status": TrendRunStatus.QUEUED.value}
    except Exception as e:
        logger.error("scheduled_discovery_failed", error=str(e))
        return {"status": "failed", "error": str(e)}
