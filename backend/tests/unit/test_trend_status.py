"""Unit tests for trend status transitions."""

import pytest

from app.modules.trends.enums import TrendStatus


class TestTrendStatusTransitions:
    """Verify the state machine defined in TrendStatus."""

    def test_discovered_to_analyzed(self):
        assert TrendStatus.DISCOVERED.can_transition_to(TrendStatus.ANALYZED)

    def test_discovered_to_scored_invalid(self):
        assert not TrendStatus.DISCOVERED.can_transition_to(TrendStatus.SCORED)

    def test_analyzed_to_scored(self):
        assert TrendStatus.ANALYZED.can_transition_to(TrendStatus.SCORED)

    def test_scored_to_prompt_generated(self):
        assert TrendStatus.SCORED.can_transition_to(TrendStatus.PROMPT_GENERATED)

    def test_prompt_generated_to_pending_review(self):
        assert TrendStatus.PROMPT_GENERATED.can_transition_to(TrendStatus.PENDING_REVIEW)

    def test_pending_review_to_approved(self):
        assert TrendStatus.PENDING_REVIEW.can_transition_to(TrendStatus.APPROVED)

    def test_pending_review_to_rejected(self):
        assert TrendStatus.PENDING_REVIEW.can_transition_to(TrendStatus.REJECTED)

    def test_pending_review_to_regeneration(self):
        """Request regeneration returns to prompt_generated state."""
        assert TrendStatus.PENDING_REVIEW.can_transition_to(TrendStatus.PROMPT_GENERATED)

    def test_approved_to_archived(self):
        assert TrendStatus.APPROVED.can_transition_to(TrendStatus.ARCHIVED)

    def test_approved_to_rejected_invalid(self):
        """Cannot reject an already approved trend."""
        assert not TrendStatus.APPROVED.can_transition_to(TrendStatus.REJECTED)

    def test_rejected_to_pending_review(self):
        """Rejected trends can be sent back for review."""
        assert TrendStatus.REJECTED.can_transition_to(TrendStatus.PENDING_REVIEW)

    def test_archived_is_terminal(self):
        """Archived is terminal — cannot transition anywhere."""
        for status in TrendStatus:
            assert not TrendStatus.ARCHIVED.can_transition_to(status)

    def test_is_reviewable(self):
        assert TrendStatus.PENDING_REVIEW.is_reviewable
        assert not TrendStatus.DISCOVERED.is_reviewable
        assert not TrendStatus.APPROVED.is_reviewable

    def test_is_terminal(self):
        assert TrendStatus.APPROVED.is_terminal
        assert TrendStatus.REJECTED.is_terminal
        assert TrendStatus.ARCHIVED.is_terminal
        assert not TrendStatus.DISCOVERED.is_terminal
        assert not TrendStatus.PENDING_REVIEW.is_terminal
