"""Unit tests for the scoring service."""

import pytest

from app.modules.scoring.services import ScoringService


class TestScoringCalculation:
    """Test the deterministic scoring formula."""

    def _make_service(self):
        # ScoringService.calculate_score is a pure method, no DB needed
        return ScoringService(config_repo=None, signal_repo=None)

    def test_basic_weighted_score(self):
        service = self._make_service()
        signals = {
            "freshness": 90.0,
            "velocity": 80.0,
            "engagement_quality": 70.0,
            "winsta_relevance": 85.0,
            "visual_generatability": 75.0,
            "novelty": 60.0,
        }
        weights = {
            "freshness": 20.0,
            "velocity": 20.0,
            "engagement_quality": 15.0,
            "winsta_relevance": 20.0,
            "visual_generatability": 15.0,
            "novelty": 10.0,
        }
        score = service.calculate_score(signals, weights)
        # Manual: (90*20 + 80*20 + 70*15 + 85*20 + 75*15 + 60*10) / 100 = 78.75
        assert score == 78.75

    def test_zero_weights(self):
        service = self._make_service()
        signals = {"freshness": 100.0}
        weights = {"freshness": 0.0}
        score = service.calculate_score(signals, weights)
        assert score == 0.0

    def test_empty_signals(self):
        service = self._make_service()
        score = service.calculate_score({}, {"freshness": 20.0})
        assert score == 0.0

    def test_perfect_score(self):
        service = self._make_service()
        signals = {k: 100.0 for k in ["a", "b", "c"]}
        weights = {"a": 40.0, "b": 30.0, "c": 30.0}
        score = service.calculate_score(signals, weights)
        assert score == 100.0

    def test_single_signal(self):
        service = self._make_service()
        signals = {"freshness": 75.0}
        weights = {"freshness": 100.0}
        score = service.calculate_score(signals, weights)
        assert score == 75.0

    def test_partial_signals(self):
        """Signals that don't have matching weights are ignored."""
        service = self._make_service()
        signals = {"freshness": 80.0, "unknown_signal": 50.0}
        weights = {"freshness": 100.0}
        # unknown_signal has 0 weight, only freshness counts
        score = service.calculate_score(signals, weights)
        assert score == 80.0
