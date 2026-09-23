"""Pipeline — Normalizer service.

Normalizes raw candidate data from different platforms into
a consistent internal format.
"""

import re
from typing import Optional

from app.collectors.base import TrendCandidateData


class NormalizerService:
    """Normalizes raw candidate data across platforms."""

    def normalize(self, candidate: TrendCandidateData) -> TrendCandidateData:
        """Normalize a candidate's fields."""
        candidate.title = self._normalize_text(candidate.title)
        candidate.caption = self._normalize_text(candidate.caption)
        candidate.hashtags = self._normalize_hashtags(candidate.hashtags)
        candidate.engagement_rate = self._calculate_engagement_rate(candidate)
        return candidate

    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove zero-width characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        return text

    def _normalize_hashtags(self, hashtags: Optional[list[str]]) -> Optional[list[str]]:
        if not hashtags:
            return hashtags
        normalized = []
        for tag in hashtags:
            tag = tag.strip().lstrip('#').lower()
            if tag and tag not in normalized:
                normalized.append(tag)
        return normalized

    def _calculate_engagement_rate(self, candidate: TrendCandidateData) -> Optional[float]:
        """Recalculate engagement rate if we have the raw metrics."""
        views = candidate.view_count or 0
        if views == 0:
            return candidate.engagement_rate

        interactions = (
            (candidate.like_count or 0)
            + (candidate.comment_count or 0)
            + (candidate.share_count or 0)
        )
        return round((interactions / views) * 100, 2)
