"""Scoring module enums."""

from enum import Enum


class SignalType(str, Enum):
    """Types of scoring signals."""
    FRESHNESS = "freshness"
    VELOCITY = "velocity"
    ENGAGEMENT_QUALITY = "engagement_quality"
    WINSTA_RELEVANCE = "winsta_relevance"
    VISUAL_GENERATABILITY = "visual_generatability"
    NOVELTY = "novelty"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()

    @classmethod
    def default_weights(cls) -> dict["SignalType", float]:
        """Default scoring weights summing to 100."""
        return {
            cls.FRESHNESS: 20.0,
            cls.VELOCITY: 20.0,
            cls.ENGAGEMENT_QUALITY: 15.0,
            cls.WINSTA_RELEVANCE: 20.0,
            cls.VISUAL_GENERATABILITY: 15.0,
            cls.NOVELTY: 10.0,
        }
