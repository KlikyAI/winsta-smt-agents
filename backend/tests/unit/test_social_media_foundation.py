"""Unit tests for the Social Media AI Agent foundation contracts."""

import pytest
from cryptography.fernet import Fernet
from types import SimpleNamespace

from app.modules.social_media.enums import ContentItemStatus, SocialPlatform
from app.modules.social_media.schemas import CreateContentBriefRequest, ScheduleContentRequest
from app.modules.social_media.services.generation import (
    generate_ai_platform_variant,
    generate_platform_variant,
    run_variant_qa,
)
from app.modules.social_media.services.connections import callback_url, get_provider_spec, missing_provider_settings, oauth_diagnostics


def test_social_brief_accepts_multiple_target_platforms() -> None:
    request = CreateContentBriefRequest(
        title="Winsta AI launch",
        target_platforms=[SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK],
    )

    assert request.target_platforms == [SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK]
    assert request.language == "en"


def test_social_brief_supports_indonesian_english_and_arabic() -> None:
    request = CreateContentBriefRequest(
        title="Multilingual brief",
        target_platforms=[SocialPlatform.INSTAGRAM],
        languages=["id", "en", "ar"],
    )

    assert request.language == "id"
    assert request.languages == ["id", "en", "ar"]


def test_social_brief_rejects_unsupported_language() -> None:
    with pytest.raises(ValueError, match="id, en, or ar"):
        CreateContentBriefRequest(
            title="Unsupported language brief",
            target_platforms=[SocialPlatform.INSTAGRAM],
            language="fr",
        )


def test_social_brief_rejects_duplicate_platforms() -> None:
    with pytest.raises(ValueError, match="must not contain duplicates"):
        CreateContentBriefRequest(
            title="Duplicate platforms",
            target_platforms=[SocialPlatform.INSTAGRAM, SocialPlatform.INSTAGRAM],
        )


def test_only_ready_content_can_be_approved() -> None:
    assert ContentItemStatus.READY_FOR_APPROVAL.is_approvable
    assert not ContentItemStatus.DRAFT.is_approvable
    assert ContentItemStatus.APPROVED.is_schedulable
    assert not ContentItemStatus.READY_FOR_APPROVAL.is_schedulable


def test_generated_x_variant_respects_platform_limit_and_passes_qa() -> None:
    variant = generate_platform_variant(
        title="Peluncuran Winsta Social Media AI",
        objective="Explain the value of content automation for marketing teams. " * 20,
        audience="business owners and social media managers",
        tone="professional and warm",
        language="en",
        platform="x",
    )
    qa_result = run_variant_qa(variant)

    assert len(variant["caption"]) <= 280
    assert variant["format"] == "text_post"
    assert qa_result["status"] == "passed"
    assert qa_result["score"] == 100


def test_generated_variants_are_adapted_per_platform() -> None:
    instagram = generate_platform_variant(
        title="Winsta AI",
        objective=None,
        audience=None,
        tone=None,
        language="en",
        platform="instagram",
    )
    tiktok = generate_platform_variant(
        title="Winsta AI",
        objective=None,
        audience=None,
        tone=None,
        language="en",
        platform="tiktok",
    )

    assert instagram["format"] == "carousel"
    assert tiktok["format"] == "short_video"
    assert instagram["hook"] != tiktok["hook"]


@pytest.mark.parametrize("language, expected", [("id", "ide"), ("en", "idea"), ("ar", "فكرة")])
def test_generated_variants_are_native_per_language(language: str, expected: str) -> None:
    variant = generate_platform_variant(
        title="Winsta AI",
        objective=None,
        audience=None,
        tone=None,
        language=language,
        platform="instagram",
    )

    assert variant["language"] == language
    assert expected in variant["hook"]
    assert run_variant_qa(variant)["status"] == "passed"


@pytest.mark.asyncio
async def test_ai_generation_falls_back_without_breaking_contract(monkeypatch) -> None:
    from app.modules.ai.services import service as ai_service_module

    async def unavailable(*args, **kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(ai_service_module.ai_service, "generate", unavailable)
    variant = await generate_ai_platform_variant(
        title="Winsta AI",
        objective=None,
        audience=None,
        tone=None,
        language="ar",
        platform="linkedin",
    )

    assert variant["language"] == "ar"
    assert variant["generation_metadata"]["mode"] == "deterministic"
    assert variant["generation_metadata"]["fallback_reason"] == "RuntimeError"


def test_schedule_requires_timezone_aware_datetime() -> None:
    with pytest.raises(ValueError, match="timezone offset"):
        ScheduleContentRequest(scheduled_at="2026-08-25T12:00:00", timezone="Asia/Jakarta")


def test_connection_readiness_exposes_setting_names_not_secret_values() -> None:
    spec = get_provider_spec("instagram")
    assert spec is not None
    settings = SimpleNamespace(
        meta_app_id="configured-app-id",
        meta_app_secret=None,
        meta_login_config_id=None,
        instagram_app_id=None,
        instagram_app_secret=None,
        social_token_encryption_key=None,
    )

    missing = missing_provider_settings(settings, spec)  # type: ignore[arg-type]

    assert missing == ["INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET", "SOCIAL_TOKEN_ENCRYPTION_KEY"]
    assert "configured-app-id" not in missing


def test_connection_callback_is_backend_owned() -> None:
    settings = SimpleNamespace(social_oauth_callback_base_url="https://api.winsta.example/")

    assert callback_url(settings, "tiktok") == "https://api.winsta.example/api/v1/social/connections/oauth/callback"  # type: ignore[arg-type]


def test_oauth_diagnostics_validate_shared_configuration_without_leaking_secrets() -> None:
    secret_values = {
        "meta_app_id": "meta-app-id-secret",
        "meta_app_secret": "meta-app-secret-value",
        "meta_login_config_id": "meta-config-secret",
        "tiktok_client_key": "tiktok-key-secret",
        "tiktok_client_secret": "tiktok-secret-value",
        "google_client_id": "google-client-secret",
        "google_client_secret": "google-secret-value",
        "x_client_id": "x-client-secret",
        "x_client_secret": "x-secret-value",
        "linkedin_client_id": "linkedin-client-secret",
        "linkedin_client_secret": "linkedin-secret-value",
        "instagram_app_id": "instagram-app-id-secret",
        "instagram_app_secret": "instagram-app-secret-value",
        "threads_app_id": "threads-app-id-secret",
        "threads_app_secret": "threads-app-secret-value",
    }
    settings = SimpleNamespace(
        **secret_values,
        meta_client_id=None,
        meta_client_secret=None,
        social_token_encryption_key=Fernet.generate_key().decode(),
        social_oauth_callback_base_url="https://bookmind.my.id",
        social_frontend_base_url="https://bookmind.my.id",
        is_production=True,
    )

    result = oauth_diagnostics(settings)  # type: ignore[arg-type]

    assert result["automatic_checks_passed"] is True
    assert result["callback_url"] == "https://bookmind.my.id/api/v1/social/connections/oauth/callback"
    assert all(item["server_configured"] for item in result["providers"])
    meta = next(item for item in result["providers"] if item["platform"] == "instagram")
    assert any("Instagram" in check for check in meta["manual_checks"])
    serialized = str(result)
    assert not any(secret in serialized for secret in secret_values.values())


def test_oauth_diagnostics_reject_invalid_production_transport_and_encryption() -> None:
    settings = SimpleNamespace(
        meta_app_id=None,
        meta_app_secret=None,
        meta_client_id=None,
        meta_client_secret=None,
        meta_login_config_id=None,
        tiktok_client_key=None,
        tiktok_client_secret=None,
        google_client_id=None,
        google_client_secret=None,
        x_client_id=None,
        x_client_secret=None,
        linkedin_client_id=None,
        linkedin_client_secret=None,
        social_token_encryption_key="invalid-key",
        social_oauth_callback_base_url="http://bookmind.my.id",
        social_frontend_base_url="not-a-url",
        is_production=True,
    )

    result = oauth_diagnostics(settings)  # type: ignore[arg-type]

    assert result["automatic_checks_passed"] is False
    assert result["token_encryption_ready"] is False
    assert "The production OAuth callback must use HTTPS." in result["issues"]
    assert "SOCIAL_FRONTEND_BASE_URL must be an absolute URL." in result["issues"]
