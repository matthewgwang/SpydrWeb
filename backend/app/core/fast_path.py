"""Fast-path filter — quickly clear low-risk transactions without full pipeline.

ALL conditions must be true for a transaction to skip the deep-analysis layers.
"""

from __future__ import annotations

from app.config import settings
from app.models.account import AccountProfile
from app.models.layers import LayerSignal
from app.models.transaction import Transaction


class FastPathFilter:
    def should_fast_path(
        self,
        rules_signals: list[LayerSignal],
        sender_profile: AccountProfile,
        receiver_profile: AccountProfile | None,
        transaction: Transaction,
        graph_signals: list[dict] | None = None,
    ) -> bool:
        if any(s.triggered for s in rules_signals):
            return False

        if sender_profile.baseline is None:
            return False

        baseline = sender_profile.baseline
        if baseline.days_of_history < settings.FAST_PATH_MIN_PROFILE_AGE_DAYS:
            return False

        # Receiver must also be well-established
        if receiver_profile and receiver_profile.baseline:
            if receiver_profile.baseline.days_of_history < settings.FAST_PATH_MIN_PROFILE_AGE_DAYS:
                return False

        # Transaction amount within 2 std (using abs z-score)
        if baseline.std_amount > 0:
            z_score = abs(transaction.amount - baseline.avg_amount) / baseline.std_amount
            if z_score > settings.FAST_PATH_MAX_AMOUNT_STD:
                return False

        if transaction.receiver_id not in sender_profile.known_payees:
            return False

        if graph_signals and any(s.get("suspicious", False) for s in graph_signals):
            return False

        # Sender vulnerability must be low (threshold 0.4)
        if sender_profile.vulnerability and sender_profile.vulnerability.score > 0.4:
            return False

        return True
