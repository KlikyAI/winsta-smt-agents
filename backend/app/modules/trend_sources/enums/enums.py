"""Trend Sources module enums."""

from enum import Enum


class CollectorType(str, Enum):
    """Type of collector used for trend discovery."""
    API = "api"
    SCRAPER = "scraper"
    RSS = "rss"
    WEBHOOK = "webhook"
    MANUAL = "manual"
