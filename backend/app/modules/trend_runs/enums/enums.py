"""Trend Runs module enums."""

from enum import Enum


class TrendRunStatus(str, Enum):
    """Status of a trend discovery run."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").title()

    @property
    def is_terminal(self) -> bool:
        """Whether this status represents a final state."""
        return self in (
            TrendRunStatus.COMPLETED,
            TrendRunStatus.PARTIALLY_COMPLETED,
            TrendRunStatus.FAILED,
            TrendRunStatus.CANCELLED,
        )

    @property
    def is_active(self) -> bool:
        return self in (TrendRunStatus.QUEUED, TrendRunStatus.RUNNING)


class TriggerType(str, Enum):
    """How a trend run was triggered."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"
