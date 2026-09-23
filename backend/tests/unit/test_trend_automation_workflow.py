"""Unit tests for the LangGraph trend automation workflow."""

from datetime import datetime, timezone

import pytest

from app.collectors.base import TrendCandidateData
from app.modules.ai.agents.trend_workflow import TrendAutomationWorkflow


def _complete_prompts() -> dict[str, str]:
    return {
        "text_to_image": "Detailed commercial image prompt with composition and lighting guidance.",
        "text_to_video": "Detailed cinematic video prompt with camera movement and scene direction.",
        "text_to_voice": "Detailed voiceover script with tone, pacing, and pronunciation guidance.",
        "image_to_image": "Detailed image transformation prompt preserving composition and identity.",
        "image_to_video": "Detailed animation prompt with controlled motion and camera direction.",
        "video_to_video": "Detailed video restyling prompt preserving temporal consistency.",
        "negative_prompt": "low quality, watermark, malformed composition",
    }


def _official_candidate(**overrides) -> TrendCandidateData:
    data = {
        "platform": "youtube",
        "external_id": "video-123",
        "canonical_url": "https://youtube.example/watch/video-123",
        "title": "AI Visual Campaign Breakout",
        "caption": "AI visual campaign ideas are accelerating across creator communities.",
        "hashtags": ["AI", "Visual", "Campaign"],
        "published_at": datetime.now(timezone.utc),
        "view_count": 1_000_000,
        "like_count": 100_000,
        "comment_count": 10_000,
        "share_count": 20_000,
        "engagement_rate": 13.0,
        "media_type": "video",
        "raw_payload": {"data_quality": "official_api"},
        "language": "en",
    }
    data.update(overrides)
    return TrendCandidateData(**data)


@pytest.mark.asyncio
async def test_verified_candidate_reaches_pending_review():
    calls = []

    async def generator(**kwargs):
        calls.append(kwargs)
        return _complete_prompts(), "test-provider", "test-model"

    workflow = TrendAutomationWorkflow(generator)
    result = await workflow.run(
        _official_candidate(),
        category="ai_visual",
        aesthetic="minimalist_organic",
        score_threshold=70.0,
    )

    assert result["status"] == "pending_review"
    assert result["evidence_verified"] is True
    assert result["overall_score"] >= 70.0
    assert result["quality_score"] >= 70.0
    assert result["validation_errors"] == []
    assert result["prompt_provider"] == "test-provider"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_synthetic_candidate_requires_verification_and_skips_prompt_generation():
    called = False

    async def generator(**kwargs):
        nonlocal called
        called = True
        return _complete_prompts(), "test-provider", "test-model"

    candidate = _official_candidate(
        external_id="ai:generated",
        raw_payload={"data_quality": "llm_agent_synthesized"},
        view_count=None,
        like_count=None,
        comment_count=None,
        share_count=None,
        engagement_rate=None,
    )
    result = await TrendAutomationWorkflow(generator).run(
        candidate,
        category="ai_visual",
        aesthetic="minimalist_organic",
        score_threshold=70.0,
    )

    assert result["status"] == "needs_verification"
    assert result["verification_reason"] == "llm_agent_synthesized"
    assert called is False


@pytest.mark.asyncio
async def test_duplicate_candidate_stops_before_enrichment_and_generation():
    called = False

    async def generator(**kwargs):
        nonlocal called
        called = True
        return _complete_prompts(), "test-provider", "test-model"

    result = await TrendAutomationWorkflow(generator).run(
        _official_candidate(),
        category="ai_visual",
        aesthetic="minimalist_organic",
        score_threshold=70.0,
        existing_external_ids={"video-123"},
    )

    assert result["status"] == "duplicate"
    assert result["duplicate_reason"] == "external_id"
    assert called is False


@pytest.mark.asyncio
async def test_invalid_prompt_is_repaired_once_before_review():
    calls = []

    async def generator(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return {"text_to_image": "Detailed image prompt but other modalities are absent."}, "provider", "model"
        return _complete_prompts(), "provider", "model"

    result = await TrendAutomationWorkflow(generator).run(
        _official_candidate(),
        category="ai_visual",
        aesthetic="minimalist_organic",
        score_threshold=70.0,
    )

    assert result["status"] == "pending_review"
    assert result["validation_attempts"] == 2
    assert calls[0]["validation_feedback"] is None
    assert calls[1]["validation_feedback"]


@pytest.mark.asyncio
async def test_low_score_candidate_skips_prompt_generation():
    called = False

    async def generator(**kwargs):
        nonlocal called
        called = True
        return _complete_prompts(), "test-provider", "test-model"

    result = await TrendAutomationWorkflow(generator).run(
        _official_candidate(),
        category="unrelated_category",
        aesthetic="minimalist_organic",
        score_threshold=101.0,
    )

    assert result["status"] == "rejected_low_score"
    assert called is False


def test_graph_contains_the_domain_pipeline_nodes():
    async def generator(**kwargs):
        return _complete_prompts(), "test-provider", "test-model"

    workflow = TrendAutomationWorkflow(generator)
    node_names = set(workflow.graph.get_graph().nodes)

    assert {
        "normalize",
        "deduplicate",
        "enrich",
        "verify_evidence",
        "score",
        "generate_prompts",
        "validate_prompts",
    }.issubset(node_names)
