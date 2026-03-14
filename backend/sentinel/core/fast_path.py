"""Fast-path filter — quickly clear low-risk transactions without full pipeline."""

from __future__ import annotations

from sentinel.config import settings
from sentinel.models.account import AccountProfile
from sentinel.models.layers import LayerSignal
from sentinel.models.transaction import Transaction


class FastPathFilter:
    """Determine if a transaction can skip the deep-analysis pipeline."""

    def should_fast_path(
        self,
        rules_signals: list[LayerSignal],
        sender_profile: AccountProfile,
        receiver_profile: AccountProfile,
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

        if baseline.std_amount > 0:
            z_score = (transaction.amount - baseline.avg_amount) / baseline.std_amount
            if z_score > settings.FAST_PATH_MAX_AMOUNT_STD:
                return False

        if transaction.receiver_id not in sender_profile.known_payees:
            return False

        if sender_profile.vulnerability and sender_profile.vulnerability.score >= settings.VULNERABILITY_HIGH_THRESHOLD:
            return False

        if graph_signals:
            if any(s.get("suspicious") for s in graph_signals):
                return False

        return True
