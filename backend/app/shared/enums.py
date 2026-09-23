"""Shared enums used across multiple modules."""

from enum import Enum


class Platform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    X = "x"
    LINKEDIN = "linkedin"
    GOOGLE_TRENDS = "google_trends"


class MediaType(str, Enum):
    """Content media types."""
    IMAGE = "image"
    VIDEO = "video"
    REEL = "reel"
    SHORT = "short"
    STORY = "story"
    CAROUSEL = "carousel"
    TEXT = "text"
    MIXED = "mixed"
