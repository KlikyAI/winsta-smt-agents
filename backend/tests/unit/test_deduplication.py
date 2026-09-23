"""Unit tests for the deduplication service."""

import pytest

from app.pipeline.deduplicator import DeduplicationService


class TestDeduplication:
    def setup_method(self):
        self.dedup = DeduplicationService(similarity_threshold=0.85)

    def test_content_hash(self):
        h1 = self.dedup.compute_content_hash("AI Art Trends", "Great content")
        h2 = self.dedup.compute_content_hash("AI Art Trends", "Great content")
        h3 = self.dedup.compute_content_hash("Different Title", "Great content")
        assert h1 == h2
        assert h1 != h3

    def test_content_hash_case_insensitive(self):
        h1 = self.dedup.compute_content_hash("AI Art", "content")
        h2 = self.dedup.compute_content_hash("ai art", "CONTENT")
        assert h1 == h2

    def test_duplicate_by_external_id(self):
        existing = {"ext_001", "ext_002"}
        assert self.dedup.is_duplicate_by_external_id("ext_001", existing)
        assert not self.dedup.is_duplicate_by_external_id("ext_003", existing)

    def test_duplicate_by_url(self):
        existing = {"https://example.com/1"}
        assert self.dedup.is_duplicate_by_url("https://example.com/1", existing)
        assert not self.dedup.is_duplicate_by_url("https://example.com/2", existing)

    def test_similar_title(self):
        existing = ["AI Generated Art Photography Trends"]
        # Very similar title
        result = self.dedup.is_similar_title(
            "AI Generated Art Photography Trend",
            existing,
        )
        assert result is not None

    def test_dissimilar_title(self):
        existing = ["AI Generated Art Photography Trends"]
        result = self.dedup.is_similar_title(
            "Cooking Recipes for Beginners",
            existing,
        )
        assert result is None

    def test_similar_hashtags(self):
        existing = [{"aiart", "photography", "trending"}]
        assert self.dedup.is_similar_hashtags(
            ["aiart", "photography", "trending", "new"],
            existing,
        )

    def test_dissimilar_hashtags(self):
        existing = [{"cooking", "recipes", "food"}]
        assert not self.dedup.is_similar_hashtags(
            ["aiart", "photography"],
            existing,
        )

    def test_check_all_no_duplicate(self):
        is_dup, reason = self.dedup.check_all(
            external_id="new_id",
            canonical_url="https://new.url",
            title="Completely New Title",
            content_hash="new_hash",
            hashtags=["newtag"],
            existing_external_ids=set(),
            existing_urls=set(),
            existing_hashes=set(),
            existing_titles=[],
            existing_hashtag_sets=[],
        )
        assert not is_dup
        assert reason == ""

    def test_check_all_duplicate_by_hash(self):
        is_dup, reason = self.dedup.check_all(
            external_id="new_id",
            canonical_url="https://new.url",
            title="New Title",
            content_hash="existing_hash",
            hashtags=[],
            existing_external_ids=set(),
            existing_urls=set(),
            existing_hashes={"existing_hash"},
            existing_titles=[],
            existing_hashtag_sets=[],
        )
        assert is_dup
        assert reason == "content_hash"
