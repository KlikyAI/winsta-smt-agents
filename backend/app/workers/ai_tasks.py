"""Celery tasks for replayable AI analysis and prompt operations."""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from pydantic import ValidationError
from sqlalchemy import select

from app.core.database import get_celery_task_session
from app.modules.ai.services.service import ai_service
from app.modules.prompt_generation.models import PromptPackage
from app.modules.prompt_generation.schemas import PromptPackageGeneratedOutput
from app.modules.trends.enums import TrendStatus
from app.modules.trends.models import Trend
from app.pipeline.enricher import ValidatorService
from app.workers.celery_app import celery_app

logger = structlog.get_logger()

MODALITY_FIELDS = (
    "text_to_image_prompt",
    "text_to_video_prompt",
    "text_to_voice_prompt",
    "image_to_image_prompt",
    "image_to_video_prompt",
    "video_to_video_prompt",
)


@celery_app.task(name="app.workers.ai_tasks.analyze_trend", bind=True, max_retries=3, default_retry_delay=30)
def analyze_trend(self, trend_id: str) -> dict:
    """Analyze and classify a persisted trend through the configured AI router."""
    logger.info("ai_analysis_started", trend_id=trend_id)

    async def execute():
        async with get_celery_task_session() as session:
            trend = await _get_trend(session, trend_id)
            if not trend:
                return {"trend_id": trend_id, "stage": "not_found"}
            response = await ai_service.generate(
                capability="trend_analysis",
                system_prompt=(
                    "Analyze a social trend. Return only JSON with description, core_concept, "
                    "category, risk_level, and risk_flags. Never invent audience metrics."
                ),
                prompt=f"Title: {trend.title}\nDescription: {trend.description or ''}",
                response_format="json",
                temperature=0.2,
            )
            analysis = _parse_json_object(response.content)
            trend.description = str(analysis.get("description") or trend.description or "")
            trend.core_concept = str(analysis.get("core_concept") or trend.core_concept or "")
            trend.category = str(analysis.get("category") or trend.category or "other")
            trend.risk_level = str(analysis.get("risk_level") or trend.risk_level or "low")
            trend.status = TrendStatus.ANALYZED.value
            await session.commit()
            return {
                "trend_id": trend_id,
                "stage": "analyzed",
                "provider": response.provider,
                "model": response.model,
                "risk_flags": analysis.get("risk_flags") or [],
            }

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.ai_tasks.extract_concepts", bind=True, max_retries=3, default_retry_delay=30)
def extract_concepts(self, trend_id: str) -> dict:
    """Extract reusable concepts and store the canonical concept summary."""
    logger.info("concept_extraction_started", trend_id=trend_id)

    async def execute():
        async with get_celery_task_session() as session:
            trend = await _get_trend(session, trend_id)
            if not trend:
                return {"trend_id": trend_id, "stage": "not_found"}
            response = await ai_service.generate(
                capability="concept_extraction",
                system_prompt="Return only JSON with keys core_concept and concepts (an array of short strings).",
                prompt=f"Trend: {trend.title}\nContext: {trend.description or ''}",
                response_format="json",
                temperature=0.2,
            )
            output = _parse_json_object(response.content)
            concepts = [str(item).strip() for item in output.get("concepts", []) if str(item).strip()]
            trend.core_concept = str(output.get("core_concept") or ", ".join(concepts) or trend.core_concept or "")
            trend.status = TrendStatus.ANALYZED.value
            await session.commit()
            return {"trend_id": trend_id, "stage": "concepts_extracted", "concepts": concepts}

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.ai_tasks.generate_prompt_package", bind=True, max_retries=3, default_retry_delay=30)
def generate_prompt_package(self, trend_id: str) -> dict:
    """Generate, validate, repair, and persist a versioned prompt package."""
    logger.info("prompt_generation_started", trend_id=trend_id)
    try:
        return asyncio.run(_generate_and_persist_prompt(trend_id, force_new_version=False))
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.ai_tasks.validate_prompt", bind=True, max_retries=3, default_retry_delay=15)
def validate_prompt(self, prompt_package_id: str) -> dict:
    """Revalidate a stored prompt package and update its workflow state."""
    logger.info("prompt_validation_started", prompt_package_id=prompt_package_id)

    async def execute():
        async with get_celery_task_session() as session:
            package = (
                await session.execute(
                    select(PromptPackage).where(
                        PromptPackage.id == uuid.UUID(prompt_package_id),
                        PromptPackage.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if not package:
                return {"prompt_package_id": prompt_package_id, "stage": "not_found"}
            payload = _package_model_payload(package)
            errors, quality_score, risk_flags = _validate_package(payload)
            package.quality_score = quality_score
            package.risk_flags = risk_flags
            package.validation_status = "passed" if not errors else "failed"
            trend = await _get_trend(session, str(package.trend_id))
            if trend:
                trend.status = TrendStatus.PENDING_REVIEW.value if not errors else TrendStatus.PROMPT_GENERATED.value
            await session.commit()
            return {
                "prompt_package_id": prompt_package_id,
                "stage": "validated" if not errors else "validation_failed",
                "quality_score": quality_score,
                "errors": errors,
            }

    try:
        return asyncio.run(execute())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(name="app.workers.ai_tasks.regenerate_prompt_package", bind=True, max_retries=3, default_retry_delay=30)
def regenerate_prompt_package(self, trend_id: str) -> dict:
    """Create a new validated prompt version without overwriting history."""
    logger.info("prompt_regeneration_started", trend_id=trend_id)
    try:
        return asyncio.run(_generate_and_persist_prompt(trend_id, force_new_version=True))
    except Exception as exc:
        raise self.retry(exc=exc)


async def _generate_and_persist_prompt(trend_id: str, *, force_new_version: bool) -> dict:
    from app.workers.collect_tasks import generate_6_modality_prompts_async

    async with get_celery_task_session() as session:
        trend = await _get_trend(session, trend_id)
        if not trend:
            return {"trend_id": trend_id, "stage": "not_found"}
        latest = (
            await session.execute(
                select(PromptPackage)
                .where(PromptPackage.trend_id == trend.id, PromptPackage.deleted_at.is_(None))
                .order_by(PromptPackage.version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        if latest and not force_new_version:
            return {
                "trend_id": trend_id,
                "stage": "already_generated",
                "prompt_package_id": str(latest.id),
                "version": latest.version,
            }

        feedback: list[str] | None = None
        validated_payload: dict[str, Any] | None = None
        provider = ""
        model = ""
        quality_score = 0.0
        risk_flags: list[str] = []
        for _attempt in range(2):
            prompts, provider, model = await generate_6_modality_prompts_async(
                title=trend.title,
                caption=trend.description or "",
                tags=[],
                category=trend.category or "general",
                validation_feedback=feedback,
            )
            payload = _generated_payload(trend, prompts)
            feedback, quality_score, risk_flags = _validate_package(payload)
            if not feedback:
                validated_payload = PromptPackageGeneratedOutput.model_validate(payload).model_dump()
                break
        if validated_payload is None:
            raise ValueError(f"Prompt validation failed after repair: {feedback}")

        version = (latest.version + 1) if latest else 1
        package = PromptPackage(
            trend_id=trend.id,
            version=version,
            trend_title=validated_payload["trend_title"],
            description=validated_payload.get("description"),
            core_concept=validated_payload.get("core_concept"),
            category=validated_payload.get("category"),
            generation_modes=validated_payload.get("generation_modes"),
            text_to_image_prompt=validated_payload.get("text_to_image_prompt"),
            image_prompt=validated_payload.get("image_prompt"),
            text_to_video_prompt=validated_payload.get("text_to_video_prompt"),
            text_to_voice_prompt=validated_payload.get("text_to_voice_prompt"),
            image_to_image_prompt=validated_payload.get("image_to_image_prompt"),
            image_to_video_prompt=validated_payload.get("image_to_video_prompt"),
            video_to_video_prompt=validated_payload.get("video_to_video_prompt"),
            negative_prompt=validated_payload.get("negative_prompt"),
            tags=validated_payload.get("tags"),
            quality_score=quality_score,
            risk_flags=risk_flags,
            ai_provider=provider,
            ai_model=model,
            template_version="langgraph-v1",
            validation_status="passed",
            generated_at=datetime.now(timezone.utc),
        )
        session.add(package)
        trend.status = TrendStatus.PENDING_REVIEW.value
        await session.commit()
        await session.refresh(package)
        return {
            "trend_id": trend_id,
            "stage": "regenerated" if force_new_version else "prompt_generated",
            "prompt_package_id": str(package.id),
            "version": version,
            "quality_score": quality_score,
        }


async def _get_trend(session, trend_id: str) -> Trend | None:
    return (
        await session.execute(select(Trend).where(Trend.id == uuid.UUID(trend_id), Trend.deleted_at.is_(None)))
    ).scalar_one_or_none()


def _parse_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    parsed = json.loads(text.strip())
    if not isinstance(parsed, dict):
        raise ValueError("AI response must be a JSON object")
    return parsed


def _generated_payload(trend: Trend, prompts: dict[str, Any]) -> dict[str, Any]:
    return {
        "trend_title": trend.title,
        "description": trend.description or "",
        "core_concept": trend.core_concept or trend.description or trend.title,
        "category": trend.category or "general",
        "generation_modes": [field.removesuffix("_prompt") for field in MODALITY_FIELDS],
        "text_to_image_prompt": prompts.get("text_to_image", ""),
        "image_prompt": prompts.get("text_to_image", ""),
        "text_to_video_prompt": prompts.get("text_to_video", ""),
        "text_to_voice_prompt": prompts.get("text_to_voice", ""),
        "image_to_image_prompt": prompts.get("image_to_image", ""),
        "image_to_video_prompt": prompts.get("image_to_video", ""),
        "video_to_video_prompt": prompts.get("video_to_video", ""),
        "negative_prompt": prompts.get("negative_prompt", ""),
        "tags": [],
        "quality_score": 0.0,
        "risk_flags": [],
    }


def _package_model_payload(package: PromptPackage) -> dict[str, Any]:
    return {
        "trend_title": package.trend_title,
        "description": package.description or "",
        "core_concept": package.core_concept or "",
        "category": package.category or "",
        "generation_modes": package.generation_modes or [],
        "text_to_image_prompt": package.text_to_image_prompt or "",
        "image_prompt": package.image_prompt or "",
        "text_to_video_prompt": package.text_to_video_prompt or "",
        "text_to_voice_prompt": package.text_to_voice_prompt or "",
        "image_to_image_prompt": package.image_to_image_prompt or "",
        "image_to_video_prompt": package.image_to_video_prompt or "",
        "video_to_video_prompt": package.video_to_video_prompt or "",
        "negative_prompt": package.negative_prompt or "",
        "tags": package.tags or [],
        "quality_score": package.quality_score or 0.0,
        "risk_flags": package.risk_flags or [],
    }


def _validate_package(payload: dict[str, Any]) -> tuple[list[str], float, list[str]]:
    errors: list[str] = []
    try:
        PromptPackageGeneratedOutput.model_validate(payload)
    except ValidationError as exc:
        errors.extend(error["msg"] for error in exc.errors())
    valid, service_errors = ValidatorService().validate_prompt_package(payload)
    if not valid:
        errors.extend(service_errors)
    missing = [field for field in MODALITY_FIELDS if not str(payload.get(field) or "").strip()]
    errors.extend(f"Missing {field}" for field in missing)
    errors = list(dict.fromkeys(errors))
    lengths = [len(str(payload.get(field) or "")) for field in MODALITY_FIELDS]
    quality_score = round(min(100.0, ((6 - len(missing)) / 6) * 70 + min(30, sum(lengths) / 72)), 1)
    risk_flags = [error for error in errors if "Blocked term" in error]
    return errors, quality_score, risk_flags
