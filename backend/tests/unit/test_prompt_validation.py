"""Unit tests for prompt package schema validation."""

import pytest

from app.modules.prompt_generation.schemas import PromptPackageGeneratedOutput
from app.pipeline.enricher import EnricherService, ValidatorService


class TestPromptSchemaValidation:
    """Test that AI output is validated through Pydantic before storage."""

    def test_valid_output(self):
        data = {
            "trend_title": "AI Visual Art Trend",
            "description": "A trending concept",
            "core_concept": "AI-powered visual creation",
            "category": "ai_visual",
            "generation_modes": ["text_to_image", "image_to_video"],
            "image_prompt": "A surreal landscape created by artificial intelligence",
            "negative_prompt": "blurry, low quality, distorted",
            "image_to_video_prompt": "Animate the landscape with flowing clouds",
            "text_to_video_prompt": "Create a video of AI-generated landscapes",
            "tags": ["ai", "visual", "art"],
            "quality_score": 85.0,
            "risk_flags": [],
        }
        output = PromptPackageGeneratedOutput(**data)
        assert output.trend_title == "AI Visual Art Trend"
        assert output.quality_score == 85.0

    def test_minimal_valid_output(self):
        """Minimum required fields."""
        output = PromptPackageGeneratedOutput(trend_title="Test")
        assert output.trend_title == "Test"
        assert output.image_prompt == ""
        assert output.tags == []

    def test_missing_required_field(self):
        """trend_title is required."""
        with pytest.raises(Exception):
            PromptPackageGeneratedOutput()


class TestPromptValidator:
    def setup_method(self):
        self.validator = ValidatorService()

    def test_valid_package(self):
        data = {
            "trend_title": "Test Trend",
            "image_prompt": "A beautiful AI-generated landscape with mountains and rivers",
        }
        is_valid, errors = self.validator.validate_prompt_package(data)
        assert is_valid
        assert errors == []

    def test_missing_image_prompt(self):
        data = {"trend_title": "Test"}
        is_valid, errors = self.validator.validate_prompt_package(data)
        assert not is_valid
        assert "Missing image_prompt" in errors

    def test_short_prompt(self):
        data = {"trend_title": "Test", "image_prompt": "short"}
        is_valid, errors = self.validator.validate_prompt_package(data)
        assert not is_valid

    def test_blocked_content(self):
        data = {
            "trend_title": "Test",
            "image_prompt": "A normal prompt with explicit content detected",
        }
        is_valid, errors = self.validator.validate_prompt_package(data)
        assert not is_valid
        assert any("explicit" in e for e in errors)


def test_enricher_adds_deterministic_metadata_without_changing_evidence():
    payload = {"data_quality": "official_api", "provider_record": {"id": "abc"}}
    enriched = EnricherService().enrich({
        "title": "Viral AI visual campaign",
        "caption": "Kreator membuat visual yang innovative untuk brand.",
        "language": None,
        "raw_payload": payload,
    })

    assert enriched["language"] == "id"
    assert enriched["raw_payload"]["data_quality"] == "official_api"
    assert enriched["raw_payload"]["provider_record"] == {"id": "abc"}
    assert enriched["raw_payload"]["enrichment"]["suggested_category"] == "ai_visual"
