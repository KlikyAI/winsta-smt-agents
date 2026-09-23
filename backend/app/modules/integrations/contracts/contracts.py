"""Integrations module — contracts and adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class IntegrationPayload:
    """Standard payload sent to downstream systems."""
    trend_id: str
    prompt_package_id: Optional[str] = None
    score: Optional[float] = None
    approved_at: Optional[str] = None
    source: str = "prompt-trends-automation"
    data: Optional[dict[str, Any]] = None


@dataclass
class IntegrationResult:
    """Result of an integration delivery attempt."""
    success: bool
    status_code: Optional[int] = None
    response_body: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class IntegrationAdapterContract(ABC):
    """Abstract base for integration adapters."""

    @property
    @abstractmethod
    def integration_name(self) -> str:
        ...

    @abstractmethod
    async def deliver(self, payload: IntegrationPayload) -> IntegrationResult:
        ...

    @abstractmethod
    async def is_configured(self) -> bool:
        ...
