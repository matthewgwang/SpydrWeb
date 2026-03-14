"""Baseline computer — computes rolling behavioural statistics for accounts."""

from __future__ import annotations

from sentinel.models.account import BaselineStats


class BaselineComputer:
    def __init__(self, decay_factor: float = 0.05) -> None:
        self.decay_factor = decay_factor

    def compute(
        self,
        account_id: str,
        events: list,
        transactions: list,
    ) -> BaselineStats:
        """Compute baseline stats from historical events and transactions.

        Full exponential-decay implementation comes in Phase 1.
        For now, compute simple averages.
        """
        if not transactions:
            return BaselineStats(decay_factor=self.decay_factor)

        amounts = [tx.amount for tx in transactions]
        avg = sum(amounts) / len(amounts)
        variance = sum((a - avg) ** 2 for a in amounts) / len(amounts)
        std = variance**0.5

        return BaselineStats(
            avg_amount=avg,
            std_amount=std,
            avg_daily_frequency=len(transactions) / max(1, self._days_span(transactions)),
            days_of_history=self._days_span(transactions),
            decay_factor=self.decay_factor,
        )

    @staticmethod
    def _days_span(transactions: list) -> int:
        if len(transactions) < 2:
            return 1
        timestamps = sorted(tx.timestamp for tx in transactions)
        delta = timestamps[-1] - timestamps[0]
        return max(1, delta.days)
