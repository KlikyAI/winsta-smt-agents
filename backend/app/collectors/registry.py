"""Collector registry — factory for platform-specific collectors."""

from typing import Optional

from app.collectors.base import TrendCollector
from app.collectors.instagram import InstagramCollector
from app.collectors.tiktok import TikTokCollector
from app.collectors.youtube import YouTubeCollector
from app.collectors.x_platform import XCollector
from app.collectors.linkedin import LinkedInCollector
from app.collectors.google_trends import GoogleTrendsCollector
from app.shared.enums import Platform


_COLLECTORS: dict[str, type[TrendCollector]] = {
    Platform.INSTAGRAM.value: InstagramCollector,
    Platform.TIKTOK.value: TikTokCollector,
    Platform.YOUTUBE.value: YouTubeCollector,
    Platform.X.value: XCollector,
    Platform.LINKEDIN.value: LinkedInCollector,
    Platform.GOOGLE_TRENDS.value: GoogleTrendsCollector,
}


def get_collector(platform: str) -> Optional[TrendCollector]:
    """Get collector instance for a platform."""
    collector_cls = _COLLECTORS.get(platform)
    if collector_cls:
        return collector_cls()
    return None


def get_all_collectors() -> dict[str, TrendCollector]:
    """Get all collector instances."""
    return {name: cls() for name, cls in _COLLECTORS.items()}
