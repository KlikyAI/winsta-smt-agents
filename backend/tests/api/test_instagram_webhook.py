"""API tests for the public Instagram webhook endpoint."""

import hashlib
import hmac
import importlib
import json
from types import SimpleNamespace

import pytest


router_module = importlib.import_module("app.modules.social_media.controllers.router")
VERIFY_TOKEN = "test-instagram-webhook-token"
APP_SECRET = "test-instagram-app-secret"


def _settings(*, verify_token: str | None = VERIFY_TOKEN, app_secret: str | None = APP_SECRET):
    return SimpleNamespace(
        instagram_webhook_verify_token=verify_token,
        instagram_app_secret=app_secret,
    )


@pytest.mark.asyncio
async def test_instagram_webhook_returns_meta_challenge(client, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "get_settings", lambda: _settings())

    response = await client.get(
        "/api/v1/social/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


@pytest.mark.asyncio
async def test_instagram_webhook_rejects_wrong_verification_token(client, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "get_settings", lambda: _settings())

    response = await client.get(
        "/api/v1/social/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_instagram_webhook_accepts_valid_signed_event(client, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "get_settings", lambda: _settings())
    body = json.dumps(
        {"object": "instagram", "entry": [{"changes": [{"field": "comments", "value": {}}]}]},
        separators=(",", ":"),
    ).encode()
    signature = "sha256=" + hmac.new(APP_SECRET.encode(), body, hashlib.sha256).hexdigest()

    response = await client.post(
        "/api/v1/social/webhooks/instagram",
        content=body,
        headers={"content-type": "application/json", "x-hub-signature-256": signature},
    )

    assert response.status_code == 200
    assert response.text == "EVENT_RECEIVED"


@pytest.mark.asyncio
async def test_instagram_webhook_rejects_invalid_signature(client, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "get_settings", lambda: _settings())

    response = await client.post(
        "/api/v1/social/webhooks/instagram",
        content=b'{"object":"instagram","entry":[]}',
        headers={"content-type": "application/json", "x-hub-signature-256": "sha256=invalid"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_instagram_webhook_fails_closed_without_app_secret(client, monkeypatch) -> None:
    monkeypatch.setattr(router_module, "get_settings", lambda: _settings(app_secret=None))

    response = await client.post(
        "/api/v1/social/webhooks/instagram",
        content=b'{"object":"instagram","entry":[]}',
        headers={"content-type": "application/json", "x-hub-signature-256": "sha256=anything"},
    )

    assert response.status_code == 503
