"""Trends module enums."""

from enum import Enum


class TrendStatus(str, Enum):
    """Lifecycle status of a canonical trend."""
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    SCORED = "scored"
    PROMPT_GENERATED = "prompt_generated"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()

    @property
    def is_terminal(self) -> bool:
        return self in (TrendStatus.APPROVED, TrendStatus.REJECTED, TrendStatus.ARCHIVED)

    @property
    def is_reviewable(self) -> bool:
        return self == TrendStatus.PENDING_REVIEW

    @classmethod
    def allowed_transitions(cls) -> dict["TrendStatus", list["TrendStatus"]]:
        """Define valid status transitions — prevents arbitrary mutation."""
        return {
            cls.DISCOVERED: [cls.ANALYZED, cls.ARCHIVED],
            cls.ANALYZED: [cls.SCORED, cls.ARCHIVED],
            cls.SCORED: [cls.PROMPT_GENERATED, cls.ARCHIVED],
            cls.PROMPT_GENERATED: [cls.PENDING_REVIEW, cls.ARCHIVED],
            cls.PENDING_REVIEW: [cls.APPROVED, cls.REJECTED, cls.PROMPT_GENERATED],
            cls.APPROVED: [cls.ARCHIVED],
            cls.REJECTED: [cls.PENDING_REVIEW, cls.ARCHIVED],
            cls.ARCHIVED: [],
        }

    def can_transition_to(self, target: "TrendStatus") -> bool:
        allowed = self.allowed_transitions().get(self, [])
        return target in allowed


class TrendCategory(str, Enum):
    """Content categories for trends."""
    AI_VISUAL = "ai_visual"
    PRODUCT_MARKETING = "product_marketing"
    LIFESTYLE = "lifestyle"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    FASHION = "fashion"
    FOOD = "food"
    TECHNOLOGY = "technology"
    TRAVEL = "travel"
    FITNESS = "fitness"
    OTHER = "other"


class RiskLevel(str, Enum):
    """Risk assessment level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
