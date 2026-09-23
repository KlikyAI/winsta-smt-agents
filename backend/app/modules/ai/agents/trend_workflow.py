"""LangGraph workflow for deterministic trend processing and prompt validation.

Collection and database persistence remain infrastructure concerns owned by the
Celery worker. This graph owns the domain decisions between those boundaries:
normalization, deduplication, evidence verification, scoring, prompt generation,
validation/repair, and routing to human review.
"""

from __future__ import annotations

import math
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Literal, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy
from pydantic import ValidationError
from typing_extensions import TypedDict

from app.collectors.base import TrendCandidateData
from app.modules.prompt_generation.schemas import PromptPackageGeneratedOutput
from app.modules.scoring.enums import SignalType
from app.modules.scoring.services import ScoringService
from app.pipeline.deduplicator import DeduplicationService
from app.pipeline.enricher import EnricherService, ValidatorService
from app.pipeline.normalizer import NormalizerService


PromptGenerator = Callable[..., Awaitable[tuple[dict[str, Any], str, str]]]

PROMPT_MODALITIES = (
    "text_to_image",
    "text_to_video",
    "text_to_voice",
    "image_to_image",
    "image_to_video",
    "video_to_video",
)

VERIFIED_DATA_QUALITIES = {"official_api", "official_video"}
UNVERIFIED_DATA_QUALITIES = {"search_signal", "llm_agent_synthesized"}


class TrendWorkflowState(TypedDict, total=False):
    """JSON-friendly state shared by all trend automation nodes."""

    candidate: dict[str, Any]
    category: str
    aesthetic: str
    score_threshold: float
    weights: dict[str, float]
    existing_external_ids: list[str]
    existing_urls: list[str]
    existing_hashes: list[str]
    existing_titles: list[str]
    existing_hashtag_sets: list[list[str]]
    duplicate: bool
    duplicate_reason: str
    evidence_verified: bool
    verification_reason: str
    signals: dict[str, float]
    overall_score: float
    prompt_package: dict[str, Any]
    prompt_provider: str
    prompt_model: str
    validation_errors: list[str]
    validation_attempts: int
    quality_score: float
    risk_flags: list[str]
    status: str


class TrendAutomationWorkflow:
    """Executable LangGraph pipeline for one trend candidate.

    The graph intentionally stops at ``pending_review``. Human approval is
    durable in the existing approvals tables and resumes delivery through the
    existing Celery integration task, avoiding process-local checkpoints.
    """

    def __init__(
        self,
        prompt_generator: PromptGenerator,
        *,
        normalizer: Optional[NormalizerService] = None,
        deduplicator: Optional[DeduplicationService] = None,
        enricher: Optional[EnricherService] = None,
        validator: Optional[ValidatorService] = None,
        max_validation_attempts: int = 2,
    ) -> None:
        self.prompt_generator = prompt_generator
        self.normalizer = normalizer or NormalizerService()
        self.deduplicator = deduplicator or DeduplicationService()
        self.enricher = enricher or EnricherService()
        self.validator = validator or ValidatorService()
        self.max_validation_attempts = max(1, max_validation_attempts)
        self.graph = self._build_graph()

    def _build_graph(self):
        builder = StateGraph(TrendWorkflowState)
        builder.add_node("normalize", self._normalize)
        builder.add_node("deduplicate", self._deduplicate)
        builder.add_node("enrich", self._enrich)
        builder.add_node("verify_evidence", self._verify_evidence)
        builder.add_node("score", self._score)
        builder.add_node(
            "generate_prompts",
            self._generate_prompts,
            retry_policy=RetryPolicy(
                initial_interval=0.5,
                backoff_factor=2.0,
                max_interval=4.0,
                max_attempts=3,
                jitter=True,
                retry_on=Exception,
            ),
        )
        builder.add_node("validate_prompts", self._validate_prompts)

        builder.add_edge(START, "normalize")
        builder.add_edge("normalize", "deduplicate")
        builder.add_conditional_edges(
            "deduplicate",
            self._route_after_deduplication,
            {"enrich": "enrich", "end": END},
        )
        builder.add_edge("enrich", "verify_evidence")
        builder.add_conditional_edges(
            "verify_evidence",
            self._route_after_verification,
            {"score": "score", "end": END},
        )
        builder.add_conditional_edges(
            "score",
            self._route_after_scoring,
            {"generate": "generate_prompts", "end": END},
        )
        builder.add_edge("generate_prompts", "validate_prompts")
        builder.add_conditional_edges(
            "validate_prompts",
            self._route_after_validation,
            {"repair": "generate_prompts", "end": END},
        )
        return builder.compile()

    async def run(
        self,
        candidate: TrendCandidateData | dict[str, Any],
        *,
        category: str,
        aesthetic: str,
        score_threshold: float,
        weights: Optional[dict[str, float]] = None,
        existing_external_ids: Optional[set[str]] = None,
        existing_urls: Optional[set[str]] = None,
        existing_hashes: Optional[set[str]] = None,
        existing_titles: Optional[list[str]] = None,
        existing_hashtag_sets: Optional[list[set[str]]] = None,
    ) -> TrendWorkflowState:
        candidate_data = asdict(candidate) if isinstance(candidate, TrendCandidateData) else dict(candidate)
        configured_weights = weights or {
            signal.value: weight
            for signal, weight in SignalType.default_weights().items()
        }
        initial_state: TrendWorkflowState = {
            "candidate": candidate_data,
            "category": category,
            "aesthetic": aesthetic,
            "score_threshold": score_threshold,
            "weights": configured_weights,
            "existing_external_ids": sorted(existing_external_ids or set()),
            "existing_urls": sorted(existing_urls or set()),
            "existing_hashes": sorted(existing_hashes or set()),
            "existing_titles": list(existing_titles or []),
            "existing_hashtag_sets": [sorted(tags) for tags in (existing_hashtag_sets or [])],
            "validation_errors": [],
            "validation_attempts": 0,
            "status": "raw",
        }
        return await self.graph.ainvoke(initial_state)

    def _normalize(self, state: TrendWorkflowState) -> TrendWorkflowState:
        allowed_fields = TrendCandidateData.__dataclass_fields__.keys()
        raw = {key: value for key, value in state["candidate"].items() if key in allowed_fields}
        normalized = self.normalizer.normalize(TrendCandidateData(**raw))
        candidate = asdict(normalized)
        candidate["content_hash"] = self.deduplicator.compute_content_hash(
            candidate.get("title") or "",
            candidate.get("caption") or "",
        )
        return {"candidate": candidate, "status": "normalized"}

    def _deduplicate(self, state: TrendWorkflowState) -> TrendWorkflowState:
        candidate = state["candidate"]
        duplicate, reason = self.deduplicator.check_all(
            external_id=candidate.get("external_id"),
            canonical_url=candidate.get("canonical_url"),
            title=candidate.get("title"),
            content_hash=candidate.get("content_hash"),
            hashtags=candidate.get("hashtags"),
            existing_external_ids=set(state.get("existing_external_ids", [])),
            existing_urls=set(state.get("existing_urls", [])),
            existing_hashes=set(state.get("existing_hashes", [])),
            existing_titles=state.get("existing_titles", []),
            existing_hashtag_sets=[set(tags) for tags in state.get("existing_hashtag_sets", [])],
        )
        return {
            "duplicate": duplicate,
            "duplicate_reason": reason,
            "status": "duplicate" if duplicate else "deduplicated",
        }

    def _enrich(self, state: TrendWorkflowState) -> TrendWorkflowState:
        enriched = self.enricher.enrich(dict(state["candidate"]))
        return {"candidate": enriched, "status": "enriched"}

    def _verify_evidence(self, state: TrendWorkflowState) -> TrendWorkflowState:
        candidate = state["candidate"]
        payload = candidate.get("raw_payload") or {}
        data_quality = str(payload.get("data_quality") or "unknown")

        if data_quality in UNVERIFIED_DATA_QUALITIES:
            return {
                "evidence_verified": False,
                "verification_reason": data_quality,
                "status": "needs_verification",
            }

        has_identity = bool(candidate.get("external_id") or candidate.get("canonical_url"))
        has_metrics = any(
            candidate.get(field) is not None
            for field in ("view_count", "like_count", "comment_count", "share_count", "engagement_rate")
        )
        verified = data_quality in VERIFIED_DATA_QUALITIES and has_identity and has_metrics
        return {
            "evidence_verified": verified,
            "verification_reason": "verified" if verified else f"insufficient_evidence:{data_quality}",
            "status": "verified" if verified else "needs_verification",
        }

    def _score(self, state: TrendWorkflowState) -> TrendWorkflowState:
        candidate = state["candidate"]
        signals = self._calculate_signals(candidate, state.get("category", "general"))
        scoring = ScoringService(config_repo=None, signal_repo=None)
        overall_score = scoring.calculate_score(signals, state["weights"])
        status = "scored" if overall_score >= state["score_threshold"] else "rejected_low_score"
        return {"signals": signals, "overall_score": overall_score, "status": status}

    async def _generate_prompts(self, state: TrendWorkflowState) -> TrendWorkflowState:
        candidate = state["candidate"]
        attempt = state.get("validation_attempts", 0) + 1
        prompts, provider, model = await self.prompt_generator(
            title=candidate.get("title") or "",
            caption=candidate.get("caption") or "",
            tags=candidate.get("hashtags") or [],
            aesthetic=state.get("aesthetic", "minimalist_organic"),
            category=state.get("category", "general"),
            validation_feedback=state.get("validation_errors") or None,
        )
        package_data = {
            "trend_title": candidate.get("title") or "Emerging Trend",
            "description": candidate.get("caption") or "",
            "core_concept": candidate.get("caption") or candidate.get("title") or "",
            "category": state.get("category", "general"),
            "generation_modes": list(PROMPT_MODALITIES),
            "text_to_image_prompt": prompts.get("text_to_image", ""),
            "image_prompt": prompts.get("text_to_image", ""),
            "text_to_video_prompt": prompts.get("text_to_video", ""),
            "text_to_voice_prompt": prompts.get("text_to_voice", ""),
            "image_to_image_prompt": prompts.get("image_to_image", ""),
            "image_to_video_prompt": prompts.get("image_to_video", ""),
            "video_to_video_prompt": prompts.get("video_to_video", ""),
            "negative_prompt": prompts.get("negative_prompt", ""),
            "tags": candidate.get("hashtags") or [],
            "quality_score": 0.0,
            "risk_flags": [],
        }
        try:
            package = PromptPackageGeneratedOutput.model_validate(package_data).model_dump()
            errors: list[str] = []
        except ValidationError as exc:
            package = package_data
            errors = [error["msg"] for error in exc.errors()]
        return {
            "prompt_package": package,
            "prompt_provider": provider,
            "prompt_model": model,
            "validation_errors": errors,
            "validation_attempts": attempt,
            "status": "prompt_generated",
        }

    def _validate_prompts(self, state: TrendWorkflowState) -> TrendWorkflowState:
        package = dict(state.get("prompt_package") or {})
        valid, errors = self.validator.validate_prompt_package(package)
        errors = list(state.get("validation_errors") or []) + errors

        missing_modalities = [
            key for key in (
                "text_to_image_prompt",
                "text_to_video_prompt",
                "text_to_voice_prompt",
                "image_to_image_prompt",
                "image_to_video_prompt",
                "video_to_video_prompt",
            )
            if not str(package.get(key) or "").strip()
        ]
        errors.extend(f"Missing {key}" for key in missing_modalities)
        errors = list(dict.fromkeys(errors))

        populated = 6 - len(missing_modalities)
        prompt_lengths = [
            len(str(package.get(key) or ""))
            for key in (
                "text_to_image_prompt",
                "text_to_video_prompt",
                "text_to_voice_prompt",
                "image_to_image_prompt",
                "image_to_video_prompt",
                "video_to_video_prompt",
            )
        ]
        average_length = sum(prompt_lengths) / len(prompt_lengths)
        quality_score = round(min(100.0, (populated / 6) * 70.0 + min(30.0, average_length / 12.0)), 1)
        risk_flags = [error for error in errors if "Blocked term" in error]
        passed = valid and not errors and quality_score >= 70.0

        package["quality_score"] = quality_score
        package["risk_flags"] = risk_flags
        if passed:
            status = "pending_review"
        elif state.get("validation_attempts", 0) < self.max_validation_attempts:
            status = "repairing_prompts"
        else:
            status = "validation_failed"
        return {
            "prompt_package": package,
            "validation_errors": errors,
            "quality_score": quality_score,
            "risk_flags": risk_flags,
            "status": status,
        }

    @staticmethod
    def _route_after_deduplication(state: TrendWorkflowState) -> Literal["enrich", "end"]:
        return "end" if state.get("duplicate") else "enrich"

    @staticmethod
    def _route_after_verification(state: TrendWorkflowState) -> Literal["score", "end"]:
        return "score" if state.get("evidence_verified") else "end"

    @staticmethod
    def _route_after_scoring(state: TrendWorkflowState) -> Literal["generate", "end"]:
        return "generate" if state.get("status") == "scored" else "end"

    @staticmethod
    def _route_after_validation(state: TrendWorkflowState) -> Literal["repair", "end"]:
        return "repair" if state.get("status") == "repairing_prompts" else "end"

    @staticmethod
    def _calculate_signals(candidate: dict[str, Any], category: str) -> dict[str, float]:
        views = max(0, int(candidate.get("view_count") or 0))
        likes = max(0, int(candidate.get("like_count") or 0))
        comments = max(0, int(candidate.get("comment_count") or 0))
        shares = max(0, int(candidate.get("share_count") or 0))
        engagement_rate = max(0.0, float(candidate.get("engagement_rate") or 0.0))

        velocity = min(100.0, math.log10(views + 1) * 12.5 + math.log10(shares + 1) * 3.0)
        engagement_quality = min(100.0, engagement_rate * 8.0 + math.log10(comments + likes + 1) * 2.0)
        freshness = TrendAutomationWorkflow._freshness_score(candidate.get("published_at"))
        text = f"{candidate.get('title') or ''} {candidate.get('caption') or ''}".lower()
        category_terms = [term for term in category.replace("_", " ").lower().split() if term]
        relevance = 90.0 if category_terms and any(term in text for term in category_terms) else 65.0
        media_type = str(candidate.get("media_type") or "").lower()
        visual_generatability = 90.0 if media_type in {"image", "video", "carousel", "reel"} else 65.0
        hashtag_count = len(candidate.get("hashtags") or [])
        novelty = min(90.0, 55.0 + hashtag_count * 5.0)

        return {
            SignalType.FRESHNESS.value: round(freshness, 2),
            SignalType.VELOCITY.value: round(velocity, 2),
            SignalType.ENGAGEMENT_QUALITY.value: round(engagement_quality, 2),
            SignalType.WINSTA_RELEVANCE.value: round(relevance, 2),
            SignalType.VISUAL_GENERATABILITY.value: round(visual_generatability, 2),
            SignalType.NOVELTY.value: round(novelty, 2),
        }

    @staticmethod
    def _freshness_score(value: Any) -> float:
        if value is None:
            return 50.0
        published_at = value
        if isinstance(value, str):
            try:
                published_at = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return 50.0
        if not isinstance(published_at, datetime):
            return 50.0
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_hours = max(0.0, (datetime.now(timezone.utc) - published_at).total_seconds() / 3600)
        return max(0.0, 100.0 - min(age_hours, 168.0) / 168.0 * 100.0)
