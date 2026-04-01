"""Weighted scoring helpers for the CRO audit engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping


@dataclass(frozen=True)
class ScoreWeight:
    """Defines the weight for a CRO category in the final score."""

    name: str
    weight: float


class CROScoringEngine:
    """Calculates weighted and normalized CRO scores."""

    DEFAULT_WEIGHTS: tuple[ScoreWeight, ...] = (
        ScoreWeight("above_the_fold_clarity", 0.15),
        ScoreWeight("cta_visibility_and_strength", 0.15),
        ScoreWeight("social_proof_presence", 0.10),
        ScoreWeight("pricing_psychology", 0.10),
        ScoreWeight("mobile_usability", 0.15),
        ScoreWeight("offer_structure", 0.10),
        ScoreWeight("trust_signals", 0.10),
        ScoreWeight("urgency_and_scarcity", 0.05),
        ScoreWeight("copy_persuasion", 0.10),
    )

    def __init__(self, weights: tuple[ScoreWeight, ...] | None = None) -> None:
        self._weights = weights or self.DEFAULT_WEIGHTS

    @property
    def weights(self) -> tuple[ScoreWeight, ...]:
        return self._weights

    def calculate(self, category_scores: Mapping[str, float]) -> int:
        """Return a normalized CRO score out of 100."""

        total = 0.0
        for score_weight in self._weights:
            raw_score = float(category_scores.get(score_weight.name, 0.0))
            clamped_score = max(0.0, min(10.0, raw_score))
            total += (clamped_score / 10.0) * score_weight.weight * 100.0
        return round(total)

    def as_percentages(self) -> Dict[str, int]:
        """Expose weights in a UI friendly format."""

        return {score_weight.name: round(score_weight.weight * 100) for score_weight in self._weights}
