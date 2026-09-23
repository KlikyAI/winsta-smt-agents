"""AI module — provider abstraction contract.

The application calls logical capabilities (trend_analysis, prompt_generation)
via AIService, which routes to concrete providers. Business code never
directly calls openai/anthropic/etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator, Optional


@dataclass
class AIRequest:
    """Standardized input for AI calls."""
    capability: str
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    response_format: Optional[str] = None  # "json" for structured output
    response_schema: Optional[Any] = None  # Optional Pydantic model class or JSON schema
    stream: bool = False
    metadata: Optional[dict[str, Any]] = None


@dataclass
class AIResponse:
    """Standardized output from AI calls."""
    content: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    estimated_cost: float = 0.0
    raw_response: Optional[dict[str, Any]] = None
    structured_data: Optional[Any] = None


class AIProviderContract(ABC):
    """Abstract base for all AI providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def generate(self, request: AIRequest, model: str) -> AIResponse:
        ...

    @abstractmethod
    async def generate_stream(self, request: AIRequest, model: str) -> AsyncIterator[str]:
        """Stream generated text chunks in real-time."""
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...
