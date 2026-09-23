"""Scoring module — service.

Implements the weighted scoring formula:
  score = Σ (signal_normalized_value × signal_weight / 100)

Scoring is deterministic and testable. AI-derived signals are computed
upstream and stored as normalized values before scoring runs.
"""

import uuid

from app.core.exceptions import BadRequestException, NotFoundException
from app.modules.scoring.enums import SignalType
from app.modules.scoring.repositories import ScoringConfigurationRepository, TrendSignalRepository
from app.modules.scoring.schemas import (
    ScoringSettingsResponse,
    ScoringWeightItem,
    UpdateScoringSettingsRequest,
)


class ScoringService:
    def __init__(
        self,
        config_repo: ScoringConfigurationRepository,
        signal_repo: TrendSignalRepository,
    ) -> None:
        self.config_repo = config_repo
        self.signal_repo = signal_repo

    async def get_settings(self) -> ScoringSettingsResponse:
        configs = await self.config_repo.get_active_config()
        version = await self.config_repo.get_current_version()

        weights = [
            ScoringWeightItem(
                signal_type=c.signal_type,
                weight=c.weight,
                description=c.description,
            )
            for c in configs
        ]
        total = sum(w.weight for w in weights)
        return ScoringSettingsResponse(weights=weights, total_weight=total, version=version)

    async def update_settings(self, data: UpdateScoringSettingsRequest) -> ScoringSettingsResponse:
        if not data.validate_total():
            total = sum(w.weight for w in data.weights)
            raise BadRequestException(
                message=f"Scoring weights must sum to 100. Current total: {total}"
            )

        # Deactivate old config, create new version
        current_version = await self.config_repo.get_current_version()
        new_version = current_version + 1

        await self.config_repo.deactivate_all()

        for item in data.weights:
            await self.config_repo.create({
                "signal_type": item.signal_type,
                "weight": item.weight,
                "description": item.description,
                "version": new_version,
                "is_active": True,
            })

        return await self.get_settings()

    def calculate_score(self, signals: dict[str, float], weights: dict[str, float]) -> float:
        """Calculate weighted score from signal values and weights.

        Args:
            signals: {signal_type: normalized_value (0-100)}
            weights: {signal_type: weight}

        Returns:
            Overall score (0-100)
        """
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        score = 0.0
        for signal_type, value in signals.items():
            weight = weights.get(signal_type, 0.0)
            score += value * (weight / total_weight)

        return round(score, 2)
