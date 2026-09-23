"""Collector base interface and data structures.

All platform-specific collectors implement TrendCollector ABC
and return normalized TrendCandidateData. Provider-specific payloads
are stored in raw_payload but don't leak through the rest of the app.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class TrendCollectionRequest:
    """Input for a collection run."""
    categories: list[str] = field(default_factory=list)
    market: str = "global"
    language: str = "en"
    limit: int = 100


@dataclass
class TrendCandidateData:
    """Normalized candidate data from any platform."""
    platform: str
    external_id: Optional[str] = None
    canonical_url: Optional[str] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[list[str]] = None
    author_name: Optional[str] = None
    published_at: Optional[datetime] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    share_count: Optional[int] = None
    engagement_rate: Optional[float] = None
    media_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    raw_payload: Optional[dict[str, Any]] = None
    language: Optional[str] = None


class TrendCollector(ABC):
    """Abstract base for platform-specific trend collectors."""

    @property
    @abstractmethod
    def platform_name(self) -> str:
        ...

    @abstractmethod
    async def collect(self, request: TrendCollectionRequest) -> list[TrendCandidateData]:
        ...

    @abstractmethod
    async def is_configured(self) -> bool:
        ...
