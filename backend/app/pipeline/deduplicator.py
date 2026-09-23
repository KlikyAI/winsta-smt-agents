"""Pipeline — Deduplication service.

Extensible deduplication with multiple strategies.
Designed so vector similarity can be added later without restructuring.
"""

import hashlib
from difflib import SequenceMatcher
from typing import Optional

import structlog

logger = structlog.get_logger()


class DeduplicationService:
    """Checks for duplicate trend candidates using multiple strategies."""

    def __init__(self, similarity_threshold: float = 0.85) -> None:
        self.similarity_threshold = similarity_threshold

    def compute_content_hash(self, title: str, caption: str = "") -> str:
        """Compute a content hash for exact-duplicate detection."""
        normalized = f"{title.strip().lower()}|{caption.strip().lower()}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def is_duplicate_by_external_id(
        self,
        external_id: str,
        existing_external_ids: set[str],
    ) -> bool:
        """Check if this external provider ID already exists."""
        return external_id in existing_external_ids

    def is_duplicate_by_url(
        self,
        url: str,
        existing_urls: set[str],
    ) -> bool:
        """Check canonical URL uniqueness."""
        return url in existing_urls

    def is_duplicate_by_hash(
        self,
        content_hash: str,
        existing_hashes: set[str],
    ) -> bool:
        """Check content hash uniqueness."""
        return content_hash in existing_hashes

    def is_similar_title(
        self,
        title: str,
        existing_titles: list[str],
    ) -> Optional[str]:
        """Check normalized title similarity. Returns matching title if similar."""
        normalized = title.strip().lower()
        for existing in existing_titles:
            ratio = SequenceMatcher(None, normalized, existing.strip().lower()).ratio()
            if ratio >= self.similarity_threshold:
                return existing
        return None

    def is_similar_hashtags(
        self,
        hashtags: list[str],
        existing_hashtag_sets: list[set[str]],
        overlap_threshold: float = 0.7,
    ) -> bool:
        """Check hashtag set overlap."""
        if not hashtags:
            return False
        current_set = {h.lower() for h in hashtags}
        for existing_set in existing_hashtag_sets:
            if not existing_set:
                continue
            intersection = current_set & existing_set
            union = current_set | existing_set
            jaccard = len(intersection) / len(union) if union else 0
            if jaccard >= overlap_threshold:
                return True
        return False

    def check_all(
        self,
        *,
        external_id: Optional[str],
        canonical_url: Optional[str],
        title: Optional[str],
        content_hash: Optional[str],
        hashtags: Optional[list[str]],
        existing_external_ids: set[str],
        existing_urls: set[str],
        existing_hashes: set[str],
        existing_titles: list[str],
        existing_hashtag_sets: list[set[str]],
    ) -> tuple[bool, str]:
        """Run all deduplication checks. Returns (is_dup, reason)."""
        if external_id and self.is_duplicate_by_external_id(external_id, existing_external_ids):
            return True, "external_id"
        if canonical_url and self.is_duplicate_by_url(canonical_url, existing_urls):
            return True, "canonical_url"
        if content_hash and self.is_duplicate_by_hash(content_hash, existing_hashes):
            return True, "content_hash"
        if title:
            match = self.is_similar_title(title, existing_titles)
            if match:
                return True, f"similar_title:{match}"
        if hashtags and self.is_similar_hashtags(hashtags, existing_hashtag_sets):
            return True, "similar_hashtags"
        return False, ""
