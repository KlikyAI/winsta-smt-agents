import base64
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.modules.ai.services import image_generation
from app.modules.ai.services.image_generation import GeneratedImage, ImageGenerationService
from app.modules.prompt_generation.services import reference_images
from app.modules.prompt_generation.services.reference_images import TrendReferenceImageService


@pytest.mark.asyncio
async def test_cloudflare_flux_returns_decoded_image_bytes(monkeypatch) -> None:
    settings = SimpleNamespace(
        cloudflare_account_id="account-id",
        cloudflare_api_token="token",
        cloudflare_flux_model="@cf/black-forest-labs/flux-1-schnell",
        cloudflare_flux_steps=4,
    )
    expected = b"jpeg-image-bytes"
    async_client = httpx.AsyncClient

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/ai/run/@cf/black-forest-labs/flux-1-schnell")
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={"success": True, "result": {"image": base64.b64encode(expected).decode()}},
        )

    monkeypatch.setattr(image_generation, "get_settings", lambda: settings)
    monkeypatch.setattr(
        image_generation.httpx,
        "AsyncClient",
        lambda **kwargs: async_client(transport=httpx.MockTransport(handler)),
    )

    generated = await ImageGenerationService().generate(
        prompt="A clean product photo",
        aspect_ratio="16:9",
        model="cloudflare-flux",
    )

    assert generated.provider == "cloudflare-workers-ai"
    assert generated.image_bytes == expected
    assert generated.image_url == ""
    assert generated.aspect_ratio == "1:1"
    assert "image_bytes" not in generated.model_dump()


class FakePublicStorage:
    configured = True

    def __init__(self) -> None:
        self.upload = AsyncMock()

    def create_public_url(self, *, bucket: str, path: str) -> str:
        return f"https://project.supabase.co/storage/v1/object/public/{bucket}/{path}"


@pytest.mark.asyncio
async def test_reference_image_is_uploaded_to_public_bucket(monkeypatch) -> None:
    storage = FakePublicStorage()
    service = TrendReferenceImageService(storage=storage)
    monkeypatch.setattr(
        reference_images,
        "get_settings",
        lambda: SimpleNamespace(supabase_trend_reference_bucket="trend-reference-images"),
    )
    service.settings = reference_images.get_settings()
    trend_id = uuid.uuid4()
    package_id = uuid.uuid4()

    url = await service.store(
        trend_id=trend_id,
        prompt_package_id=package_id,
        generated=GeneratedImage(
            image_url="",
            provider="cloudflare-workers-ai",
            model="@cf/black-forest-labs/flux-1-schnell",
            prompt="Prompt",
            latency_ms=12,
            aspect_ratio="1:1",
            mime_type="image/jpeg",
            image_bytes=b"jpeg-image-bytes",
        ),
    )

    assert url.startswith(
        "https://project.supabase.co/storage/v1/object/public/trend-reference-images/trends/"
    )
    upload = storage.upload.await_args.kwargs
    assert upload["bucket"] == "trend-reference-images"
    assert upload["content"] == b"jpeg-image-bytes"
    assert str(package_id) in upload["path"]
