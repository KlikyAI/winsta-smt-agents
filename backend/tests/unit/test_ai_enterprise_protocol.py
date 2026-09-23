"""Unit tests for the Enterprise AI Model Service Protocol.

Verifies:
1. HTTP connection pooling and lifecycle.
2. AIProviderContract streaming interface.
3. AIService real-time token streaming and multi-provider fallback.
4. Pydantic schema-guided structured generation with validation retry.
"""

from typing import AsyncIterator
import pytest
from pydantic import BaseModel, Field

from app.modules.ai.contracts import AIProviderContract, AIRequest, AIResponse
from app.modules.ai.providers.http_client import close_ai_http_clients, get_ai_http_client
from app.modules.ai.services.service import AIService


class DummySchema(BaseModel):
    title: str = Field(..., description="Post title")
    virality_score: int = Field(..., ge=0, le=100)
    hashtags: list[str] = Field(default_factory=list)


class MockHealthyProvider(AIProviderContract):
    def __init__(self, name: str = "mock_healthy") -> None:
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    async def is_available(self) -> bool:
        return True

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        if request.response_format == "json":
            content = '{"title": "Viral Trend 2026", "virality_score": 95, "hashtags": ["#viral", "#ai"]}'
        else:
            content = f"Response from {self._name} using {model}"
        return AIResponse(
            content=content,
            provider=self.provider_name,
            model=model,
            input_tokens=10,
            output_tokens=20,
            latency_ms=15,
        )

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        for token in ["Hello", " ", "from", " ", self._name]:
            yield token


class MockFailingProvider(AIProviderContract):
    def __init__(self, name: str = "mock_failing") -> None:
        self._name = name

    @property
    def provider_name(self) -> str:
        return self._name

    async def is_available(self) -> bool:
        return True

    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        raise RuntimeError("Service temporarily overloaded (503)")

    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        raise RuntimeError("Streaming connection failed (502)")
        yield ""  # pragma: no cover


@pytest.mark.asyncio
async def test_ai_contracts_data_structures():
    """Verify AIRequest and AIResponse support streaming and schema fields."""
    req = AIRequest(
        capability="test",
        prompt="hello",
        response_schema=DummySchema,
        stream=True,
    )
    assert req.stream is True
    assert req.response_schema == DummySchema

    resp = AIResponse(
        content="test",
        provider="mock",
        model="m-1",
        structured_data=DummySchema(title="T", virality_score=80),
    )
    assert resp.structured_data.title == "T"
    assert resp.structured_data.virality_score == 80


@pytest.mark.asyncio
async def test_http_connection_pool_lifecycle():
    """Verify persistent HTTP connection pooling and graceful closure."""
    client1 = await get_ai_http_client(timeout_seconds=30.0)
    client2 = await get_ai_http_client(timeout_seconds=30.0)
    # Both calls should share the exact same client instance
    assert client1 is client2
    assert not client1.is_closed

    # Verify connection limits
    assert client1._transport._pool._max_keepalive_connections == 50

    # Shutdown
    await close_ai_http_clients()
    assert client1.is_closed


@pytest.mark.asyncio
async def test_ai_service_streaming():
    """Verify real-time streaming tokens are yielded correctly."""
    mock = MockHealthyProvider("deepseek")
    service = AIService(providers={"deepseek": mock})

    tokens = []
    async for token in service.generate_stream(
        capability="test",
        prompt="stream test",
        provider_name="deepseek",
        model_name="deepseek-chat",
    ):
        tokens.append(token)

    assert "".join(tokens) == "Hello from deepseek"


@pytest.mark.asyncio
async def test_ai_service_streaming_fallback():
    """Verify streaming smoothly falls back to secondary provider if primary fails."""
    primary = MockFailingProvider("deepseek")
    fallback = MockHealthyProvider("openai")

    service = AIService(providers={"deepseek": primary, "openai": fallback})
    service._memory_runtime_settings = {
        "ai_provider": "deepseek",
        "ai_fallback_provider": "openai",
    }

    tokens = []
    async for token in service.generate_stream(
        capability="test",
        prompt="fallback stream",
        provider_name="deepseek",
    ):
        tokens.append(token)

    assert "".join(tokens) == "Hello from openai"


@pytest.mark.asyncio
async def test_ai_service_structured_output():
    """Verify generate_structured parses output into a validated Pydantic model."""
    mock = MockHealthyProvider("deepseek")
    service = AIService(providers={"deepseek": mock})

    result: DummySchema = await service.generate_structured(
        capability="test",
        prompt="Give me viral score",
        schema=DummySchema,
        provider_name="deepseek",
    )

    assert isinstance(result, DummySchema)
    assert result.title == "Viral Trend 2026"
    assert result.virality_score == 95
    assert "#viral" in result.hashtags
