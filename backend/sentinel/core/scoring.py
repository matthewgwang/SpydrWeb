"""Score computer — aggregates layer signals into a single confidence score."""

from __future__ import annotations

from sentinel.config import settings
from sentinel.models.layers import LayerSignal
from sentinel.models.report import Action


class ScoreComputer:
    """Compute a confidence score from layer signals + adjustments, then map to an Action."""

    def compute(
        self,
        layer_signals: list[LayerSignal],
        layer_weights: dict[int, float] | None = None,
        vulnerability_score: float = 0.0,
        velocity_deviation: float = 1.0,
    ) -> float:
        if not layer_signals:
            return 0.0

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

        base = weighted_sum / total_weight if total_weight else 0.0

        corroboration = min(len(triggered) - 1, 3) * settings.CORROBORATION_BONUS
        velocity_adj = (velocity_deviation - 1.0) * settings.VELOCITY_MULTIPLIER_WEIGHT

        score = base + corroboration + velocity_adj
        return max(0.0, min(score, 1.0))

    def get_recommended_action(self, score: float) -> Action:
        if score >= settings.SCORE_THRESHOLD_REFER:
            return Action.REFER
        if score >= settings.SCORE_THRESHOLD_HOLD:
            return Action.HOLD
        if score >= settings.SCORE_THRESHOLD_DELAY:
            return Action.DELAY
        return Action.ALLOW
