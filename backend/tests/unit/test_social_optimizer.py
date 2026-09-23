import uuid

from app.modules.social_media.schemas import UpdateBrandKitRequest
from app.modules.social_media.services.generation import (
    generate_platform_variant,
    run_variant_qa,
)
from app.modules.social_media.services.performance import (
    PerformanceSample,
    calculate_performance_insights,
)


def test_brand_brain_is_applied_to_deterministic_variant() -> None:
    variant = generate_platform_variant(
        title="Responsible automation",
        objective="Explain how teams can automate safely.",
        audience=None,
        tone=None,
        language="en",
        platform="linkedin",
        brand_context={
            "version": 4,
            "tone": "Practical and evidence-led",
            "target_audience": "operations leaders",
            "default_hashtags": ["#ResponsibleAI"],
            "disclaimer": "Human reviewed.",
            "required_terms": ["Winsta AI"],
        },
    )

    assert "Practical and evidence-led" in variant["caption"]
    assert "operations leaders" in variant["caption"]
    assert "Human reviewed." in variant["caption"]
    assert "Winsta AI" in variant["caption"]
    assert "#ResponsibleAI" in variant["hashtags"]
    assert variant["generation_metadata"]["brand_kit_version"] == 4


def test_brand_policy_qa_reports_forbidden_and_missing_required_terms() -> None:
    qa = run_variant_qa(
        {
            "platform": "x",
            "language": "en",
            "caption": "A guaranteed shortcut.",
            "hook": "Try this",
            "cta": "Learn more",
            "hashtags": [],
            "media_ref": "https://cdn.example/image.png",
        },
        {
            "version": 2,
            "forbidden_terms": ["guaranteed"],
            "required_terms": ["Winsta AI"],
        },
    )

    assert qa["status"] == "failed"
    assert qa["checks"]["brand_forbidden_terms_absent"] is False
    assert qa["checks"]["brand_required_terms_present"] is False
    assert qa["policy"]["forbidden_hits"] == ["guaranteed"]


def test_brand_kit_schema_normalizes_policy_values() -> None:
    brand = UpdateBrandKitRequest(
        brand_name="Winsta",
        default_hashtags=["WinstaAI", "#WinstaAI", " social AI "],
        forbidden_terms=[" guaranteed ", "guaranteed"],
        languages=["ID", "en-US", "ar"],
    )

    assert brand.default_hashtags == ["#WinstaAI", "#socialAI"]
    assert brand.forbidden_terms == ["guaranteed"]
    assert brand.languages == ["id", "en", "ar"]


def test_performance_analyzer_builds_overall_and_segment_experiment() -> None:
    samples = [
        PerformanceSample(
            publish_job_id=uuid.uuid4(),
            platform="instagram",
            language="id",
            content_format="carousel",
            metrics={"views": 1000, "likes": 80, "comments": 10, "shares": 10},
        )
        for _ in range(3)
    ]

    insights = calculate_performance_insights(samples)

    assert len(insights) == 2
    overall = insights[0]
    segment = insights[1]
    assert overall.platform is None
    assert overall.engagement_rate == 10
    assert overall.confidence == 0.3
    assert segment.platform == "instagram"
    assert segment.recommendations[0]["experiment"]["approval_required"] is True
    assert segment.recommendations[0]["action"] == "create_controlled_challenger"


def test_performance_analyzer_normalizes_platform_metric_aliases() -> None:
    samples = [
        PerformanceSample(
            publish_job_id=uuid.uuid4(),
            platform="facebook",
            language="en",
            content_format="feed_post",
            metrics={
                "post_impressions": 2000,
                "post_engaged_users": 100,
                "post_reactions_by_type_total": {"like": 70, "love": 20},
            },
        )
    ]

    overall = calculate_performance_insights(samples)[0]

    # The platform-provided engaged-user total wins over reaction components,
    # preventing aliases from being counted twice.
    assert overall.engagement_rate == 5
    assert overall.evidence["total_engagements"] == 100
