"""Score computer — aggregates layer signals into a single confidence score.

Uses the multiplicative formula from the spec:
  score = (weighted_sum + corroboration_bonus * (n_triggered - 1)) * vuln_multiplier * vel_multiplier
"""

from __future__ import annotations

from app.config import settings
from app.models.layers import LayerSignal
from app.models.report import Action


class ScoreComputer:
    def compute(
        self,
        layer_signals: list[LayerSignal],
        layer_weights: dict[int, float] | None = None,
        vulnerability_score: float = 0.0,
        velocity_deviation: float = 1.0,
    ) -> float:
        triggered = [s for s in layer_signals if s.triggered]
        if not triggered:
            return 0.0

        weights = layer_weights or {}
        total_weight = 0.0
        weighted_sum = 0.0

        for signal in triggered:
            w = weights.get(signal.layer_id, 1.0)
            weighted_sum += signal.confidence * w
            total_weight += w

        base_score = weighted_sum / max(total_weight, 1.0)

        n_triggered = len(triggered)
        corroboration = settings.CORROBORATION_BONUS * max(n_triggered - 1, 0)

        vuln_multiplier = 1.0 + (vulnerability_score * 0.3)

        vel_multiplier = 1.0
        if velocity_deviation > 1.0:
            vel_multiplier = 1.0 + min(velocity_deviation - 1.0, 2.0) * 0.05

        final_score = min(
            (base_score + corroboration) * vuln_multiplier * vel_multiplier, 1.0
        )
        return round(final_score, 3)

    def get_recommended_action(self, score: float) -> Action:
        if score >= settings.SCORE_THRESHOLD_REFER:
            return Action.REFER
        if score >= settings.SCORE_THRESHOLD_HOLD:
            return Action.HOLD
        if score >= settings.SCORE_THRESHOLD_DELAY:
            return Action.DELAY
        return Action.ALLOW
