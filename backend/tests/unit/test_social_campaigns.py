from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.modules.social_media.schemas import CreateCampaignRequest


def test_campaign_request_normalizes_currency_and_platforms() -> None:
    request = CreateCampaignRequest(
        name="Spring launch",
        objective="Conversions",
        platforms=["facebook", "instagram"],
        budget_cents=12500,
        currency="usd",
    )

    assert request.currency == "USD"
    assert [platform.value for platform in request.platforms] == ["facebook", "instagram"]


def test_campaign_request_rejects_duplicate_platforms() -> None:
    with pytest.raises(ValidationError, match="platforms must not contain duplicates"):
        CreateCampaignRequest(
            name="Duplicate targets",
            objective="Reach",
            platforms=["facebook", "facebook"],
            budget_cents=100,
        )


def test_campaign_request_rejects_backwards_schedule() -> None:
    start = datetime.now(timezone.utc)
    with pytest.raises(ValidationError, match="end_at must be later than start_at"):
        CreateCampaignRequest(
            name="Invalid schedule",
            objective="Traffic",
            platforms=["youtube"],
            budget_cents=100,
            start_at=start,
            end_at=start - timedelta(minutes=1),
        )
