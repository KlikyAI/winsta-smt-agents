"""Scoring module — Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class ScoringWeightItem(BaseModel):
    signal_type: str
    weight: float = Field(ge=0, le=100)
    description: Optional[str] = None


class ScoringSettingsResponse(BaseModel):
    weights: list[ScoringWeightItem]
    total_weight: float
    version: int


class UpdateScoringSettingsRequest(BaseModel):
    weights: list[ScoringWeightItem]

    def validate_total(self) -> bool:
        total = sum(w.weight for w in self.weights)
        return abs(total - 100.0) < 0.01
