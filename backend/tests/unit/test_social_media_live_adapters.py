import uuid
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse
from unittest.mock import AsyncMock, MagicMock, patch

from cryptography.fernet import Fernet
import pytest

from app.core.exceptions import BadRequestException
from app.modules.social_media import security
from app.modules.social_media.providers.meta import MetaGraphClient
from app.modules.social_media.providers.instagram import InstagramGraphClient
from app.modules.social_media.providers.oauth import InstagramOAuthClient, ThreadsOAuthClient, create_pkce_pair
from app.modules.social_media.providers.registry import SocialPublisherRegistry
from app.modules.social_media.services.service import SocialMediaService


def test_social_credential_is_encrypted(monkeypatch) -> None:
    key = Fernet.generate_key().decode()
    monkeypatch.setattr(security, "get_settings", lambda: SimpleNamespace(social_token_encryption_key=key))

    encrypted = security.encrypt_secret("meta-page-token")

    assert encrypted != "meta-page-token"
    assert security.decrypt_secret(encrypted) == "meta-page-token"


def test_meta_metrics_are_normalized() -> None:
    metrics = MetaGraphClient._normalize_metrics({
        "data": [
            {"name": "likes", "values": [{"value": 4}]},
            {"name": "comments", "value": 2},
        ],
    })

    assert metrics == {"likes": 4, "comments": 2}


def test_meta_business_authorization_url_uses_configuration_instead_of_scope() -> None:
    client = object.__new__(MetaGraphClient)
    client.settings = SimpleNamespace(
        meta_graph_api_version="v25.0",
        meta_app_id="app-123",
        meta_app_secret="secret",
        meta_login_config_id="config-123",
    )
    client.version = "v25.0"
    client.graph_base = "https://graph.facebook.com/v25.0"

    url = client.authorization_url(
        state="opaque-state",
        redirect_uri="https://api.example.com/api/v1/social/connections/oauth/callback",
        scopes=["instagram_basic"],
    )

    params = parse_qs(urlparse(url).query)

    assert params["client_id"] == ["app-123"]
    assert params["state"] == ["opaque-state"]
    assert params["config_id"] == ["config-123"]
    assert "response_type" not in params
    assert "override_default_response_type" not in params
    assert "scope" not in params


def test_meta_legacy_authorization_url_uses_requested_scope() -> None:
    client = object.__new__(MetaGraphClient)
    client.settings = SimpleNamespace(
        meta_graph_api_version="v25.0",
        meta_app_id="app-123",
        meta_app_secret="secret",
        meta_login_config_id=None,
    )
    client.version = "v25.0"
    client.graph_base = "https://graph.facebook.com/v25.0"

    url = client.authorization_url(
        state="opaque-state",
        redirect_uri="https://api.example.com/api/v1/social/connections/oauth/callback",
        scopes=["pages_show_list", "pages_manage_posts"],
    )
    params = parse_qs(urlparse(url).query)

    assert params["response_type"] == ["code"]
    assert params["scope"] == ["pages_show_list,pages_manage_posts"]
    assert "config_id" not in params
    assert "override_default_response_type" not in params


def test_instagram_login_authorization_url_uses_instagram_app_and_scopes() -> None:
    client = object.__new__(InstagramOAuthClient)
    client.settings = SimpleNamespace(instagram_app_id="2831347320574129", instagram_app_secret="secret")

    url = client.authorization_url(
        state="opaque-state",
        redirect_uri="https://bookmind.my.id/api/v1/social/connections/oauth/callback",
        scopes=["instagram_business_basic", "instagram_business_content_publish"],
    )
    params = parse_qs(urlparse(url).query)

    assert urlparse(url).netloc == "www.instagram.com"
    assert params["client_id"] == ["2831347320574129"]
    assert params["response_type"] == ["code"]
    assert params["scope"] == ["instagram_business_basic,instagram_business_content_publish"]


def test_tiktok_text_limits_use_utf16_code_units() -> None:
    from app.modules.social_media.providers.omnichannel import _truncate_utf16

    value = "a" * 88 + "🏎️💨"
    truncated = _truncate_utf16(value, 90)

    assert len(truncated.encode("utf-16-le")) // 2 <= 90


@pytest.mark.asyncio
async def test_instagram_login_exchange_uses_short_and_long_lived_tokens() -> None:
    client = object.__new__(InstagramOAuthClient)
    client.settings = SimpleNamespace(instagram_app_id="instagram-app", instagram_app_secret="instagram-secret")
    short_response = MagicMock(is_success=True)
    short_response.json.return_value = {"access_token": "short-token", "user_id": "ig-user"}
    long_response = MagicMock(is_success=True)
    long_response.json.return_value = {
        "access_token": "long-token",
        "user_id": "ig-user",
        "expires_in": 5_184_000,
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=short_response) as mock_post:
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=long_response) as mock_get:
            token = await client.exchange_code(
                code="auth-code",
                redirect_uri="https://bookmind.my.id/api/v1/social/connections/oauth/callback",
                scopes=["instagram_business_basic"],
            )

    assert token.access_token == "long-token"
    assert token.expires_at is not None
    assert mock_post.call_args.kwargs["data"]["grant_type"] == "authorization_code"
    assert mock_get.call_args.kwargs["params"]["grant_type"] == "ig_exchange_token"


@pytest.mark.asyncio
async def test_instagram_publish_waits_for_container_before_media_publish() -> None:
    client = object.__new__(InstagramGraphClient)
    client.graph_base = "https://graph.instagram.com"

    container_response = MagicMock(is_success=True)
    container_response.json.return_value = {"id": "container-123"}
    status_response = MagicMock(is_success=True)
    status_response.json.return_value = {"status_code": "FINISHED"}
    published_response = MagicMock(is_success=True)
    published_response.json.return_value = {"id": "media-456"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [container_response, published_response]
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=status_response) as mock_get:
            result = await client.publish(
                account_id="ig-user",
                access_token="access-token",
                media_url="https://cdn.example.com/image.jpg",
                caption="hello",
            )

    assert result == {"id": "media-456"}
    assert mock_get.await_count == 1
    assert mock_post.await_args_list[1].kwargs["params"]["creation_id"] == "container-123"


@pytest.mark.asyncio
async def test_instagram_publish_accepts_media_id_response_fallback() -> None:
    client = object.__new__(InstagramGraphClient)
    client.graph_base = "https://graph.instagram.com"

    container_response = MagicMock(is_success=True)
    container_response.json.return_value = {"media_id": "container-123"}
    status_response = MagicMock(is_success=True)
    status_response.json.return_value = {"status_code": "FINISHED"}
    published_response = MagicMock(is_success=True)
    published_response.json.return_value = {"media_id": "media-456"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [container_response, published_response]
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=status_response):
            result = await client.publish(
                account_id="ig-user",
                access_token="access-token",
                media_url="https://cdn.example.com/image.jpg",
                caption="hello",
            )

    assert result["id"] == "media-456"


@pytest.mark.asyncio
async def test_tiktok_photo_publish_uses_documented_minimal_post_info() -> None:
    from app.modules.social_media.providers.contracts import PublishContext
    from app.modules.social_media.providers.omnichannel import TikTokPublisherAdapter

    adapter = TikTokPublisherAdapter()
    context = PublishContext(
        platform="tiktok",
        account_id="tiktok-user",
        account_metadata={},
        access_token="tiktok-token",
        media_url="https://bookmind.my.id/api/v1/social/assets/asset-123/public?expires=1&signature=sig",
        caption="A TikTok photo post 🏎️💨 with a longer description",
        language="en",
        idempotency_key="tiktok-idempotency",
    )
    creator_response = MagicMock(is_success=True)
    creator_response.json.return_value = {
        "data": {
            "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
            "comment_disabled": False,
        }
    }
    init_response = MagicMock(is_success=True)
    init_response.json.return_value = {"data": {"publish_id": "publish-123"}}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [creator_response, init_response]
        result = await adapter.publish(context)

    assert result.external_post_id == "publish-123"
    post_info = mock_post.await_args_list[1].kwargs["json"]["post_info"]
    assert post_info["title"] == "A TikTok photo post 🏎️💨 with a longer description"
    assert len(post_info["title"].encode("utf-16-le")) // 2 <= 90
    assert post_info["description"] == context.caption
    assert post_info["privacy_level"] == "SELF_ONLY"
    assert post_info["disable_comment"] is False
    assert post_info["auto_add_music"] is True
    assert post_info["brand_content_toggle"] is False
    assert post_info["brand_organic_toggle"] is False


def test_threads_authorization_url_uses_threads_app() -> None:
    client = object.__new__(ThreadsOAuthClient)
    client.settings = SimpleNamespace(threads_app_id="threads-app", threads_app_secret="secret")

    url = client.authorization_url(
        state="opaque-state",
        redirect_uri="https://bookmind.my.id/api/v1/social/connections/oauth/callback",
        scopes=["threads_basic", "threads_content_publish"],
    )
    params = parse_qs(urlparse(url).query)

    assert urlparse(url).netloc == "threads.net"
    assert params["client_id"] == ["threads-app"]
    assert params["scope"] == ["threads_basic,threads_content_publish"]


@pytest.mark.asyncio
async def test_threads_publisher_creates_and_publishes_image_container() -> None:
    from app.modules.social_media.providers.contracts import PublishContext
    from app.modules.social_media.providers.threads import ThreadsPublisherAdapter

    adapter = ThreadsPublisherAdapter()
    context = PublishContext(
        platform="threads",
        account_id="threads-user",
        account_metadata={},
        access_token="threads-token",
        media_url="https://cdn.example.com/image.jpg",
        caption="A Threads post",
        language="en",
        idempotency_key="threads-idempotency",
    )
    container_response = MagicMock(is_success=True)
    container_response.json.return_value = {"id": "container-123"}
    published_response = MagicMock(is_success=True)
    published_response.json.return_value = {"id": "thread-456"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [container_response, published_response]
        result = await adapter.publish(context)

    assert result.external_post_id == "thread-456"
    assert mock_post.await_args_list[0].kwargs["params"]["media_type"] == "IMAGE"
    assert mock_post.await_args_list[1].kwargs["params"]["creation_id"] == "container-123"


@pytest.mark.asyncio
async def test_meta_granted_permissions_exclude_declined_permissions() -> None:
    client = object.__new__(MetaGraphClient)
    client.graph_base = "https://graph.facebook.com/v25.0"
    response = MagicMock()
    response.is_success = True
    response.json.return_value = {
        "data": [
            {"permission": "pages_manage_posts", "status": "granted"},
            {"permission": "pages_show_list", "status": "granted"},
            {"permission": "pages_read_engagement", "status": "declined"},
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=response):
        permissions = await client.list_granted_permissions("user-token")

    assert permissions == ["pages_manage_posts", "pages_show_list"]


@pytest.mark.asyncio
async def test_meta_connection_rejects_missing_required_permissions() -> None:
    service = object.__new__(SocialMediaService)
    client = MagicMock()
    client.exchange_code = AsyncMock(return_value={"access_token": "user-token"})
    client.list_granted_permissions = AsyncMock(
        return_value=["pages_show_list", "pages_read_engagement"]
    )
    client.list_pages = AsyncMock()
    oauth_state = SimpleNamespace(
        platform="facebook",
        redirect_uri="https://api.example.com/api/v1/social/connections/oauth/callback",
    )

    with patch(
        "app.modules.social_media.services.service.MetaGraphClient",
        return_value=client,
    ):
        with pytest.raises(BadRequestException, match="pages_manage_posts"):
            await service._complete_meta_connection(oauth_state=oauth_state, code="auth-code")

    client.list_pages.assert_not_awaited()


@pytest.mark.asyncio
async def test_meta_connection_persists_permissions_reported_by_meta() -> None:
    service = object.__new__(SocialMediaService)
    service.content_repo = SimpleNamespace(
        session=SimpleNamespace(add=MagicMock(), flush=AsyncMock())
    )
    service._upsert_connection = AsyncMock()
    granted = ["pages_manage_posts", "pages_read_engagement", "pages_show_list"]
    client = MagicMock()
    client.exchange_code = AsyncMock(return_value={"access_token": "user-token"})
    client.list_granted_permissions = AsyncMock(return_value=granted)
    client.list_pages = AsyncMock(
        return_value=[
            {
                "id": "page-123",
                "name": "Example Page",
                "access_token": "page-token",
            }
        ]
    )
    oauth_state = SimpleNamespace(
        platform="facebook",
        redirect_uri="https://api.example.com/api/v1/social/connections/oauth/callback",
        organization_id=uuid.uuid4(),
    )

    with patch(
        "app.modules.social_media.services.service.MetaGraphClient",
        return_value=client,
    ):
        await service._complete_meta_connection(oauth_state=oauth_state, code="auth-code")

    credential = service.content_repo.session.add.call_args.args[0]
    assert credential.scopes == granted


def test_publisher_registry_exposes_all_omnichannel_adapters() -> None:
    registry = SocialPublisherRegistry()

    for platform in ("instagram", "facebook", "threads", "tiktok", "youtube", "x", "linkedin"):
        assert registry.is_active(platform)


def test_x_pkce_pair_is_url_safe_and_not_plaintext() -> None:
    verifier, challenge = create_pkce_pair()

    assert len(verifier) >= 43
    assert len(challenge) == 43
    assert verifier != challenge


@pytest.mark.asyncio
async def test_x_publisher_falls_back_to_text_when_media_upload_is_forbidden() -> None:
    from app.modules.social_media.providers.omnichannel import XPublisherAdapter
    from app.modules.social_media.providers.contracts import PublishContext

    adapter = XPublisherAdapter()
    context = PublishContext(
        platform="x",
        account_id="12345",
        account_metadata={},
        access_token="fake-x-token",
        media_url="https://example.com/sample.png",
        caption="Exploring AI innovations today #AI #Tech",
        language="en",
        idempotency_key="idemp-12345",
    )

    with patch("app.modules.social_media.providers.omnichannel.download_public_media", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = (b"fake_image_bytes", "image/png")

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            upload_response = MagicMock()
            upload_response.status_code = 403
            upload_response.text = '{"title":"Forbidden","type":"about:blank","status":403,"detail":"Forbidden"}'

            tweet_response = MagicMock()
            tweet_response.is_success = True
            tweet_response.json.return_value = {"data": {"id": "tweet-98765", "text": context.caption}}

            mock_post.side_effect = [upload_response, tweet_response]

            result = await adapter.publish(context)

            assert result.external_post_id == "tweet-98765"
            assert result.response_data["provider"] == "x"
