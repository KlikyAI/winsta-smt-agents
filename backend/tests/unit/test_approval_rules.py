"""Unit tests for approval rules."""

import pytest

from app.modules.approvals.schemas import ReviewRequest


class TestApprovalRules:
    """Test that review decisions are validated."""

    def test_valid_approve(self):
        req = ReviewRequest(decision="approve", notes="Good content")
        assert req.decision == "approve"

    def test_valid_reject(self):
        req = ReviewRequest(decision="reject", notes="Not relevant")
        assert req.decision == "reject"

    def test_valid_regeneration(self):
        req = ReviewRequest(decision="request_regeneration")
        assert req.decision == "request_regeneration"

    def test_invalid_decision(self):
        """Only approve/reject/request_regeneration are valid."""
        with pytest.raises(Exception):
            ReviewRequest(decision="invalid_decision")

    def test_notes_optional(self):
        req = ReviewRequest(decision="approve")
        assert req.notes is None

    def test_scoring_weight_validation(self):
        """Scoring weights must sum to 100."""
        from app.modules.scoring.schemas import UpdateScoringSettingsRequest, ScoringWeightItem
        req = UpdateScoringSettingsRequest(weights=[
            ScoringWeightItem(signal_type="freshness", weight=50.0),
            ScoringWeightItem(signal_type="velocity", weight=50.0),
        ])
        assert req.validate_total()

    def test_scoring_weight_invalid_total(self):
        from app.modules.scoring.schemas import UpdateScoringSettingsRequest, ScoringWeightItem
        req = UpdateScoringSettingsRequest(weights=[
            ScoringWeightItem(signal_type="freshness", weight=60.0),
            ScoringWeightItem(signal_type="velocity", weight=50.0),
        ])
        assert not req.validate_total()
