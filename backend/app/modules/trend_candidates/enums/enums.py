"""Trend Candidates module enums."""

from enum import Enum


class CandidateStatus(str, Enum):
    """Status of a raw trend candidate."""
    RAW = "raw"
    NORMALIZED = "normalized"
    DEDUPLICATED = "deduplicated"
    ENRICHED = "enriched"
    DUPLICATE = "duplicate"
    NEEDS_VERIFICATION = "needs_verification"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ERROR = "error"
