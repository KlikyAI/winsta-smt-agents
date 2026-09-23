import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest

from app.modules.social_media.services import media_fetch
from app.modules.social_media.services.media_assets import MediaAssetService, SupabaseStorageClient


class FakeStorage:
    configured = True

    def __init__(self) -> None:
        self.settings = SimpleNamespace(supabase_storage_bucket="social-media-assets")
        self.upload = AsyncMock()
        self.create_signed_url = AsyncMock(return_value="https://signed.example/creative.png")


def test_supabase_object_path_preserves_folders_and_encodes_names() -> None:
    client = object.__new__(SupabaseStorageClient)
    client.settings = SimpleNamespace(supabase_url="https://project.supabase.co")

    path = client._object_path("social-media-assets", "org/launch image.png")

    assert path == (
        "https://project.supabase.co/storage/v1/object/"
        "social-media-assets/org/launch%20image.png"
    )


def test_supabase_relative_signed_url_includes_storage_api_prefix() -> None:
    client = object.__new__(SupabaseStorageClient)
    client.settings = SimpleNamespace(supabase_url="https://project.supabase.co")

    url = client._absolute_signed_url("/object/sign/social-media-assets/file.png?token=masked")

    assert url == (
        "https://project.supabase.co/storage/v1/object/sign/"
        "social-media-assets/file.png?token=masked"
    )


def test_supabase_public_url_preserves_folders_and_encodes_names() -> None:
    client = object.__new__(SupabaseStorageClient)
    client.settings = SimpleNamespace(supabase_url="https://project.supabase.co")

    url = client.create_public_url(
        bucket="trend-reference-images",
        path="trends/trend id/reference.png",
    )

    assert url == (
        "https://project.supabase.co/storage/v1/object/public/"
        "trend-reference-images/trends/trend%20id/reference.png"
    )


@pytest.mark.asyncio
async def test_media_asset_store_uploads_checksum_addressed_object() -> None:
    storage = FakeStorage()
    service = MediaAssetService(storage=storage)
    result_proxy = Mock()
    result_proxy.scalar_one_or_none.return_value = None
    session = SimpleNamespace(
        execute=AsyncMock(return_value=result_proxy),
        add=Mock(),
        flush=AsyncMock(),
    )

    stored = await service.store_bytes(
        session,
        organization_id=uuid.uuid4(),
        content=b"valid png bytes",
        mime_type="image/png",
        provider="unit-test",
    )

    assert stored.asset.sha256
    assert stored.asset.storage_path.endswith(".png")
    assert stored.signed_url == "https://signed.example/creative.png"
    assert stored.deduplicated is False
    storage.upload.assert_awaited_once()
    session.add.assert_called_once_with(stored.asset)


@pytest.mark.asyncio
async def test_remote_media_revalidates_redirect_destination(monkeypatch) -> None:
    validate = AsyncMock()
    async_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/original":
            return httpx.Response(302, headers={"Location": "/final.png"})
        return httpx.Response(200, headers={"Content-Type": "image/png"}, content=b"png")

    monkeypatch.setattr(media_fetch, "_validate_public_url", validate)
    monkeypatch.setattr(
        media_fetch.httpx,
        "AsyncClient",
        lambda **kwargs: async_client(transport=httpx.MockTransport(handler)),
    )

    content, mime_type = await media_fetch.download_public_media(
        "https://cdn.example/original"
    )

    assert content == b"png"
    assert mime_type == "image/png"
    assert [call.args[0] for call in validate.await_args_list] == [
        "https://cdn.example/original",
        "https://cdn.example/final.png",
    ]
