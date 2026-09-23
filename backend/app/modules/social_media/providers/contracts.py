"""Provider-neutral contracts for social publishing and analytics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class PublisherUnavailableError(RuntimeError):
    """Raised when a platform is configured but has no active publisher."""


@dataclass(frozen=True)
class PublishContext:
    platform: str
    account_id: str
    account_metadata: dict[str, Any]
    access_token: str
    media_url: str | None
    caption: str
    language: str
    idempotency_key: str


@dataclass(frozen=True)
class PublishResult:
    external_post_id: str
    response_data: dict[str, Any]


class SocialPublisherAdapter(ABC):
    """Stable boundary between the workflow and platform SDKs/APIs."""

    platforms: frozenset[str]
    requires_media: bool = True

    @abstractmethod
    async def publish(self, context: PublishContext) -> PublishResult:
        ...

    @abstractmethod
    async def fetch_metrics(
        self,
        *,
        platform: str,
        external_post_id: str,
        access_token: str,
    ) -> dict[str, Any]:
        ...
