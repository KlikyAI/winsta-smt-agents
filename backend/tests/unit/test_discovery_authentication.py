from types import SimpleNamespace
import base64

import pytest

from app.core.oauth_manager import OAuthTokenManager
from app.collectors.base import TrendCollectionRequest
from app.collectors.instagram import InstagramCollector


def _manager(**settings_values) -> OAuthTokenManager:
    manager = object.__new__(OAuthTokenManager)
    values = dict(
        instagram_access_token=None,
        meta_client_id="meta-client",
        meta_client_secret="meta-secret",
        meta_app_id="meta-app",
        meta_app_secret="meta-app-secret",
        tiktok_access_token=None,
        tiktok_client_key=None,
        tiktok_client_secret=None,
        x_bearer_token=None,
        x_client_id=None,
        x_client_secret=None,
        x_api_key=None,
        x_api_secret=None,
        linkedin_client_id="linkedin-client",
        linkedin_client_secret="linkedin-secret",
    )
    values.update(settings_values)
    manager.settings = SimpleNamespace(**values)
    return manager


@pytest.mark.asyncio
async def test_meta_uses_connected_social_oauth_context(monkeypatch):
    manager = _manager()

    async def connected(_platform):
        return {"access_token": "page-token", "account_id": "ig-123"}

    monkeypatch.setattr(manager, "_get_connected_social_credential", connected)

    assert await manager.get_meta_token() == "page-token"


@pytest.mark.asyncio
async def test_meta_app_credentials_are_not_treated_as_instagram_user_token(monkeypatch):
    manager = _manager()

    async def no_connected(_platform):
        return None

    async def no_source(_platform):
        return None

    monkeypatch.setattr(manager, "_get_connected_social_credential", no_connected)
    monkeypatch.setattr(manager, "_get_db_source_config", no_source)

    assert await manager.get_meta_token() is None


@pytest.mark.asyncio
async def test_linkedin_client_credentials_are_not_treated_as_member_token(monkeypatch):
    manager = _manager()

    async def no_connected(_platform):
        return None

    async def no_source(_platform):
        return None

    monkeypatch.setattr(manager, "_get_connected_social_credential", no_connected)
    monkeypatch.setattr(manager, "_get_db_source_config", no_source)

    assert await manager.get_linkedin_token() is None


@pytest.mark.asyncio
async def test_instagram_uses_connected_account_id_for_graph_api(monkeypatch):
    requested = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"data": [{"id": "hashtag-1", "name": "ai"}]}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, params):
            requested["url"] = url
            requested["params"] = params
            return FakeResponse()

    async def connected_context():
        return {"access_token": "page-token", "account_id": "ig-123"}

    monkeypatch.setattr("app.collectors.instagram.httpx.AsyncClient", FakeClient)
    monkeypatch.setattr("app.collectors.instagram.oauth_token_manager.get_meta_context", connected_context)

    items = await InstagramCollector().collect(
        TrendCollectionRequest(categories=["tech_ai"], market="id", language="en", limit=1)
    )

    assert requested["params"]["user_id"] == "ig-123"
    assert requested["params"]["access_token"] == "page-token"
    assert items[0].raw_payload["data_quality"] == "official_api"


@pytest.mark.asyncio
async def test_x_app_only_exchange_uses_api_key_not_oauth_client_id(monkeypatch):
    requested = {}

    class FakeRedis:
        async def get(self, _key):
            return None

        async def setex(self, *_args):
            return None

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"access_token": "x-bearer", "expires_in": 3600}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, headers, data):
            requested.update({"url": url, "headers": headers, "data": data})
            return FakeResponse()

    manager = _manager(
        x_client_id="oauth-client-id",
        x_client_secret="oauth-client-secret",
        x_api_key="consumer-api-key",
        x_api_secret="consumer-api-secret",
    )
    async def no_source(_platform):
        return None

    monkeypatch.setattr(manager, "_get_db_source_config", no_source)
    async def fake_get_redis():
        return FakeRedis()

    monkeypatch.setattr("app.core.oauth_manager.get_redis", fake_get_redis)
    monkeypatch.setattr("app.core.oauth_manager.httpx.AsyncClient", FakeClient)

    assert await manager.get_x_token() == "x-bearer"
    expected = base64.b64encode(b"consumer-api-key:consumer-api-secret").decode()
    assert requested["headers"]["Authorization"] == f"Basic {expected}"


@pytest.mark.asyncio
async def test_x_client_id_secret_alone_are_not_used_for_app_only_exchange(monkeypatch):
    manager = _manager(
        x_client_id="oauth-client-id",
        x_client_secret="oauth-client-secret",
        x_api_key=None,
        x_api_secret=None,
    )

    async def no_source(_platform):
        return None

    monkeypatch.setattr(manager, "_get_db_source_config", no_source)

    assert await manager.get_x_token() is None
