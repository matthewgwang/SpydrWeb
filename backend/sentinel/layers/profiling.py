"""Layer 2 — Behavioral Disruption Analysis.

Compares current transaction against the sender's baseline to detect
deviations in amount, frequency, timing, routine absences, and social
spending patterns. All checks are pure Python, no AI.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from sentinel.layers.base import DetectionLayer
from sentinel.models.events import EventType
from sentinel.models.layers import LayerSignal

if TYPE_CHECKING:
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream
    from sentinel.models.account import AccountProfile
    from sentinel.models.transaction import Transaction


class ProfilingLayer(DetectionLayer):
    layer_id = 2
    layer_name = "profiling"

    def __init__(self, baseline_computer=None, event_stream=None) -> None:
        self.baseline_computer = baseline_computer
        self.event_stream = event_stream

    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> list[LayerSignal]:
        signals: list[LayerSignal] = []

        if sender.baseline is None:
            signals.append(LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=0.3,
                explanation="No baseline available — cannot assess behavioral deviation",
                severity="low",
            ))
            return signals

        baseline = sender.baseline

        sig = self._check_amount_deviation(transaction, baseline)
        if sig:
            signals.append(sig)

        sig = self._check_frequency_deviation(
            transaction.sender_id, event_stream, baseline, transaction.timestamp
        )
        if sig:
            signals.append(sig)

        sig = self._check_time_deviation(transaction, baseline)
        if sig:
            signals.append(sig)

        sig = self._check_balance_check_absence(
            transaction.sender_id, event_stream, baseline, transaction.timestamp
        )
        if sig:
            signals.append(sig)

        sig = self._check_social_spending_decline(
            transaction.sender_id, event_stream, transaction.timestamp
        )
        if sig:
            signals.append(sig)

        if not signals:
            signals.append(LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="Transaction consistent with sender baseline",
            ))

        return signals

    def _check_amount_deviation(
        self, transaction: Transaction, baseline
    ) -> LayerSignal | None:
        if baseline.std_amount <= 0:
            return None
        z_score = abs(transaction.amount - baseline.avg_amount) / baseline.std_amount
        if z_score > 3.0:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=min(z_score / 5.0, 1.0),
                explanation=(
                    f"Transaction amount ${transaction.amount:.2f} is {z_score:.1f} "
                    f"standard deviations from baseline mean ${baseline.avg_amount:.2f}"
                ),
                evidence={"z_score": round(z_score, 2), "baseline_avg": baseline.avg_amount},
                severity="high" if z_score > 5.0 else "medium",
            )
        return None

    def _check_frequency_deviation(
        self, account_id: str, event_stream: EventStream, baseline, current_time
    ) -> LayerSignal | None:
        today_events = event_stream.query(
            account_id=account_id,
            event_type=EventType.TRANSACTION,
            since=current_time - timedelta(hours=24),
        )
        today_count = len(today_events)
        if baseline.avg_daily_frequency > 0 and today_count > baseline.avg_daily_frequency * 2:
            ratio = today_count / baseline.avg_daily_frequency
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=min(ratio / 5.0, 0.8),
                explanation=(
                    f"Transaction frequency today ({today_count}) is {ratio:.1f}x the "
                    f"daily average ({baseline.avg_daily_frequency:.1f})"
                ),
                evidence={"today_count": today_count, "avg_daily": baseline.avg_daily_frequency},
                severity="medium",
            )
        return None

    def _check_time_deviation(
        self, transaction: Transaction, baseline
    ) -> LayerSignal | None:
        hour = transaction.timestamp.hour
        if baseline.typical_hours and hour not in baseline.typical_hours:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=0.5,
                explanation=(
                    f"Transaction at {hour}:00 — customer is typically active "
                    f"during hours {baseline.typical_hours}"
                ),
                evidence={"hour": hour, "typical_hours": baseline.typical_hours},
                severity="low",
            )
        return None

    def _check_balance_check_absence(
        self, account_id: str, event_stream: EventStream, baseline, current_time
    ) -> LayerSignal | None:
        """Check if an expected daily balance check hasn't occurred."""
        if baseline.balance_check_frequency_daily <= 0:
            return None

        expected_interval_hours = 24.0 / baseline.balance_check_frequency_daily
        max_gap_hours = expected_interval_hours * 3

        recent = event_stream.query(
            account_id=account_id,
            event_type=EventType.BALANCE_CHECK,
            since=current_time - timedelta(hours=max_gap_hours),
        )
        if not recent:
            days_missing = max_gap_hours / 24
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=0.6,
                explanation=(
                    f"Expected balance_check has not occurred in {days_missing:.0f} days "
                    f"— customer typically does this {baseline.balance_check_frequency_daily:.1f}x per day"
                ),
                evidence={
                    "expected_freq": baseline.balance_check_frequency_daily,
                    "gap_hours": max_gap_hours,
                },
                severity="medium",
            )
        return None

    def _check_social_spending_decline(
        self, account_id: str, event_stream: EventStream, current_time
    ) -> LayerSignal | None:
        """Compare social spending in last 30 days vs previous 30 days."""
        social_categories = ["restaurant", "entertainment", "club", "church", "social"]

        recent_30d = event_stream.query(
            account_id=account_id,
            event_type=EventType.TRANSACTION,
            since=current_time - timedelta(days=30),
        )
        all_60d = event_stream.query(
            account_id=account_id,
            event_type=EventType.TRANSACTION,
            since=current_time - timedelta(days=60),
        )
        previous_30d = [
            e for e in all_60d if e.timestamp < current_time - timedelta(days=30)
        ]

        def count_social(events):
            return len([
                e for e in events
                if any(
                    cat in e.payload.get("merchant_category", "").lower()
                    for cat in social_categories
                )
            ])

        recent_social = count_social(recent_30d)
        previous_social = count_social(previous_30d)

        if previous_social > 3 and recent_social < previous_social * 0.5:
            decline_pct = (1 - recent_social / previous_social) * 100
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=True,
                confidence=0.4,
                explanation=(
                    f"Social spending declined: {recent_social} social transactions in "
                    f"last 30 days vs {previous_social} in previous 30 days "
                    f"({decline_pct:.0f}% decline)"
                ),
                evidence={
                    "recent_social": recent_social,
                    "previous_social": previous_social,
                },
                severity="low",
            )
        return None
