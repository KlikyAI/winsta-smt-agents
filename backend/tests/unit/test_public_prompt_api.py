import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import ValidationException
from app.main import create_app
from app.modules.prompt_generation.models import PromptPackage
from app.modules.prompt_generation.services import PromptGenerationService


def _prompt_package() -> PromptPackage:
    now = datetime.now(timezone.utc)
    package = PromptPackage(
        trend_id=uuid.uuid4(),
        version=2,
        trend_title="Public AI visual trend",
        category="ai_visual",
        validation_status="passed",
        risk_flags=["internal-only"],
        ai_provider="internal-provider",
        trend_reference_image_url="https://project.supabase.co/storage/v1/object/public/trend-reference-images/image.jpg",
    )
    package.id = uuid.uuid4()
    package.created_at = now
    package.updated_at = now
    return package


def test_public_prompt_route_has_no_auth_security_requirement() -> None:
    operation = create_app().openapi()["paths"]["/api/v1/public/prompts"]["get"]

    assert not operation.get("security")
    parameter_names = {parameter["name"] for parameter in operation["parameters"]}
    assert {
        "date_from",
        "date_to",
        "category",
        "search",
        "has_reference_image",
        "min_quality_score",
        "generation_mode",
        "latest_only",
        "sort",
        "page",
        "page_size",
    } <= parameter_names


@pytest.mark.asyncio
async def test_public_prompt_service_returns_safe_paginated_contract() -> None:
    package = _prompt_package()
    repo = SimpleNamespace(list_public=AsyncMock(return_value=([package], 1)))
    service = PromptGenerationService(repo)

    result = await service.list_public(
        page=1,
        page_size=20,
        date_from=date(2026, 8, 1),
        date_to=date(2026, 8, 25),
        category="ai_visual",
        search="visual",
        has_reference_image=True,
        min_quality_score=70,
        generation_mode="text_to_image",
        latest_only=True,
        sort="newest",
    )

    assert result.total == 1
    assert result.total_pages == 1
    assert result.items[0].trend_reference_image_url == package.trend_reference_image_url
    public_payload = result.items[0].model_dump()
    assert "risk_flags" not in public_payload
    assert "ai_provider" not in public_payload
    filters = repo.list_public.await_args.kwargs
    assert filters["date_from"].isoformat() == "2026-08-01T00:00:00+00:00"
    assert filters["date_to_exclusive"].isoformat() == "2026-08-26T00:00:00+00:00"


@pytest.mark.asyncio
async def test_public_prompt_service_rejects_reversed_date_range() -> None:
    repo = SimpleNamespace(list_public=AsyncMock())
    service = PromptGenerationService(repo)

    with pytest.raises(ValidationException, match="date_from must be on or before date_to"):
        await service.list_public(
            page=1,
            page_size=20,
            date_from=date(2026, 8, 26),
            date_to=date(2026, 8, 25),
            category=None,
            search=None,
            has_reference_image=None,
            min_quality_score=None,
            generation_mode=None,
            latest_only=True,
            sort="newest",
        )
