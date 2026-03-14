"""Baseline computer — computes rolling behavioural statistics for accounts.

Uses exponential decay weighting so recent activity contributes more
than old history: weight_i = e^(-lambda * age_in_days_i)
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Optional

from sentinel.models.account import BaselineStats
from sentinel.models.events import Event, EventType


class BaselineComputer:
    def __init__(self, decay_factor: float = 0.05) -> None:
        self.decay_factor = decay_factor

    def compute(
        self,
        account_id: str,
        events: list[Event],
        transactions: list,
        reference_time: Optional[datetime] = None,
    ) -> BaselineStats:
        """Compute baseline stats from historical events and transactions."""
        now = reference_time or datetime.now(UTC)

        if not transactions:
            return BaselineStats(decay_factor=self.decay_factor)

        avg_amount, std_amount = self._time_weighted_stats(transactions, now)

        days_span = self._days_span(transactions)
        daily_freq = len(transactions) / max(1, days_span)
        weekly_freq = daily_freq * 7

        typical_hours = self._typical_hours(transactions)
        typical_merchants = self._typical_merchants(transactions)
        typical_channels = self._typical_channels(transactions)
        typical_tx_types = self._typical_transaction_types(transactions)

        login_freq = self._event_frequency_daily(
            events, account_id, EventType.LOGIN, days_span
        )
        balance_check_freq = self._event_frequency_daily(
            events, account_id, EventType.BALANCE_CHECK, days_span
        )

        timestamps = [tx.timestamp for tx in transactions] + [e.timestamp for e in events]
        last_activity = max(timestamps) if timestamps else None

        return BaselineStats(
            avg_amount=avg_amount,
            std_amount=std_amount,
            avg_daily_frequency=daily_freq,
            avg_weekly_frequency=weekly_freq,
            typical_hours=typical_hours,
            typical_merchants=typical_merchants,
            typical_channels=typical_channels,
            typical_transaction_types=typical_tx_types,
            login_frequency_daily=login_freq,
            balance_check_frequency_daily=balance_check_freq,
            last_activity=last_activity,
            decay_factor=self.decay_factor,
            days_of_history=days_span,
        )

    def _time_weighted_stats(
        self, transactions: list, current_time: datetime
    ) -> tuple[float, float]:
        """Compute mean and std with exponential decay weighting."""
        weights: list[float] = []
        amounts: list[float] = []

        for tx in transactions:
            age_days = (current_time - tx.timestamp).total_seconds() / 86400
            weight = math.exp(-self.decay_factor * max(age_days, 0))
            weights.append(weight)
            amounts.append(tx.amount)

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.0, 0.0

        weighted_mean = sum(a * w for a, w in zip(amounts, weights)) / total_weight
        weighted_var = (
            sum(w * (a - weighted_mean) ** 2 for a, w in zip(amounts, weights))
            / total_weight
        )
        weighted_std = math.sqrt(weighted_var)

        return weighted_mean, weighted_std

    @staticmethod
    def _days_span(transactions: list) -> int:
        if len(transactions) < 2:
            return 1
        timestamps = sorted(tx.timestamp for tx in transactions)
        delta = timestamps[-1] - timestamps[0]
        return max(1, delta.days)

    @staticmethod
    def _typical_hours(transactions: list) -> list[int]:
        hours = [tx.timestamp.hour for tx in transactions]
        counts = Counter(hours)
        if not counts:
            return []
        threshold = max(counts.values()) * 0.3
        return sorted(h for h, c in counts.items() if c >= threshold)

    @staticmethod
    def _typical_merchants(transactions: list) -> dict[str, int]:
        merchants: Counter[str] = Counter()
        for tx in transactions:
            merchant = getattr(tx, "description", "") or ""
            if merchant:
                merchants[merchant] += 1
        return dict(merchants.most_common(20))

    @staticmethod
    def _typical_channels(transactions: list) -> dict[str, int]:
        channels: Counter[str] = Counter()
        for tx in transactions:
            ch = getattr(tx, "channel", "online")
            channels[ch] += 1
        return dict(channels)

    @staticmethod
    def _typical_transaction_types(transactions: list) -> dict[str, int]:
        types: Counter[str] = Counter()
        for tx in transactions:
            tx_type = getattr(tx, "type", None)
            if tx_type is not None:
                types[tx_type.value if hasattr(tx_type, "value") else str(tx_type)] += 1
        return dict(types)

    @staticmethod
    def _event_frequency_daily(
        events: list[Event], account_id: str, event_type: EventType, days_span: int
    ) -> float:
        matching = [
            e
            for e in events
            if e.account_id == account_id and e.event_type == event_type
        ]
        return len(matching) / max(1, days_span)
