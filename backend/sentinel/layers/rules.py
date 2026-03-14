"""Layer 1 — Deterministic rules engine.

Pure Python, no AI. Each rule returns a LayerSignal.
Returns a list of signals (one per triggered rule).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sentinel.layers.base import DetectionLayer
from sentinel.models.events import EventType
from sentinel.models.layers import LayerSignal
from sentinel.models.transaction import TransactionType

if TYPE_CHECKING:
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream
    from sentinel.models.account import AccountProfile
    from sentinel.models.transaction import Transaction


# Configurable thresholds
VELOCITY_THRESHOLD = 3  # transfers per hour
AMOUNT_SINGLE_THRESHOLD = 3000.0
AMOUNT_DAILY_THRESHOLD = 5000.0
NEW_PAYEE_AMOUNT_THRESHOLD = 1000.0
LAYERING_STEP_WINDOW = 3  # steps (PaySim: 1 step ≈ 1 hour)

# Placeholder blacklist — extend via config or external source
SUSPICIOUS_BLACKLIST: set[str] = set()


class RulesLayer(DetectionLayer):
    """Layer 1 — deterministic rule-based detection."""

    layer_id = 1
    layer_name = "rules"

    def __init__(self, blacklist: set[str] | None = None) -> None:
        self.blacklist = blacklist or SUSPICIOUS_BLACKLIST

    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> list[LayerSignal]:
        """Run all rules, return list of triggered signals."""
        ref_time = transaction.timestamp or datetime.utcnow()
        signals: list[LayerSignal] = []

        signals.append(
            self._check_velocity(transaction, event_stream, ref_time)
        )
        signals.append(
            self._check_amount_threshold(transaction, event_stream, ref_time)
        )
        signals.append(
            self._check_geographic_impossibility(transaction, event_stream, ref_time)
        )
        signals.append(
            self._check_new_payee_large_amount(transaction, sender)
        )
        signals.append(
            self._check_blacklist(transaction)
        )
        signals.append(
            self._check_device_change_sensitive_action(transaction, event_stream, ref_time)
        )
        signals.append(
            self._check_balance_drain(transaction, sender)
        )
        signals.append(
            self._check_layering_pattern(transaction, event_stream, ref_time)
        )

        return [s for s in signals if s.triggered]

    def _check_velocity(
        self,
        transaction: Transaction,
        event_stream: EventStream,
        ref_time: datetime,
    ) -> LayerSignal:
        """Rule: >3 transfers in 1 hour from same account."""
        cutoff = ref_time - timedelta(hours=1)
        txns = event_stream.query(
            account_id=transaction.sender_id,
            event_type=EventType.TRANSACTION,
            since=cutoff,
        )
        count = len(txns)
        triggered = count > VELOCITY_THRESHOLD
        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.85 if triggered else 0.0,
            explanation=f"{count} transfers in 1 hour from account (threshold: {VELOCITY_THRESHOLD})"
            if triggered
            else "",
            evidence={"count": count, "threshold": VELOCITY_THRESHOLD},
            severity="high" if triggered else "low",
        )

    def _check_amount_threshold(
        self,
        transaction: Transaction,
        event_stream: EventStream,
        ref_time: datetime,
    ) -> LayerSignal:
        """Rule: single transaction > $3,000 or daily total > $5,000."""
        single_triggered = transaction.amount > AMOUNT_SINGLE_THRESHOLD

        cutoff = ref_time - timedelta(hours=24)
        txns = event_stream.query(
            account_id=transaction.sender_id,
            event_type=EventType.TRANSACTION,
            since=cutoff,
        )
        daily_total = sum(
            e.payload.get("amount", 0) for e in txns if isinstance(e.payload, dict)
        )
        daily_triggered = daily_total > AMOUNT_DAILY_THRESHOLD

        triggered = single_triggered or daily_triggered
        reasons = []
        if single_triggered:
            reasons.append(f"Single transaction ${transaction.amount:,.0f} > ${AMOUNT_SINGLE_THRESHOLD:,.0f}")
        if daily_triggered:
            reasons.append(f"Daily total ${daily_total:,.0f} > ${AMOUNT_DAILY_THRESHOLD:,.0f}")

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.9 if triggered else 0.0,
            explanation="; ".join(reasons) if triggered else "",
            evidence={
                "amount": transaction.amount,
                "daily_total": daily_total,
                "single_threshold": AMOUNT_SINGLE_THRESHOLD,
                "daily_threshold": AMOUNT_DAILY_THRESHOLD,
            },
            severity="high" if triggered else "low",
        )

    def _check_geographic_impossibility(
        self,
        transaction: Transaction,
        event_stream: EventStream,
        ref_time: datetime,
    ) -> LayerSignal:
        """Rule: login from city X, transaction from city Y in impossible timeframe.

        Requires location data in event payloads. Returns not triggered if absent.
        """
        logins = event_stream.query(
            account_id=transaction.sender_id,
            event_type=EventType.LOGIN,
            since=ref_time - timedelta(hours=2),
        )
        if not logins:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="",
                evidence={},
                severity="low",
            )

        login_locations = [
            e.payload.get("location", e.payload.get("city"))
            for e in logins
            if isinstance(e.payload, dict)
        ]
        txn_location = (
            transaction.description
            or (getattr(transaction, "location", None))
        )

        if not login_locations or not txn_location:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="",
                evidence={"note": "Insufficient location data"},
                severity="low",
            )

        # Simplified: if login and txn have different city strings within 30 min, flag
        triggered = False
        for login in logins:
            delta = (ref_time - login.timestamp).total_seconds() / 60
            loc = login.payload.get("location", login.payload.get("city", "")) if isinstance(login.payload, dict) else ""
            if loc and txn_location and loc != txn_location and delta < 30:
                triggered = True
                break

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.95 if triggered else 0.0,
            explanation=f"Login location differs from transaction location within 30 minutes"
            if triggered
            else "",
            evidence={"login_count": len(logins)},
            severity="high" if triggered else "low",
        )

    def _check_new_payee_large_amount(
        self,
        transaction: Transaction,
        sender: AccountProfile,
    ) -> LayerSignal:
        """Rule: first-ever transfer to payee above $1,000."""
        is_new_payee = transaction.receiver_id not in (sender.known_payees or [])
        is_large = transaction.amount > NEW_PAYEE_AMOUNT_THRESHOLD
        triggered = is_new_payee and is_large

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.8 if triggered else 0.0,
            explanation=f"First transfer to new payee ${transaction.amount:,.0f} > ${NEW_PAYEE_AMOUNT_THRESHOLD:,.0f}"
            if triggered
            else "",
            evidence={
                "receiver_id": transaction.receiver_id,
                "amount": transaction.amount,
                "known_payees": (sender.known_payees or [])[:10],
            },
            severity="medium" if triggered else "low",
        )

    def _check_blacklist(self, transaction: Transaction) -> LayerSignal:
        """Rule: recipient on known suspicious list."""
        triggered = transaction.receiver_id in self.blacklist

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.98 if triggered else 0.0,
            explanation=f"Recipient {transaction.receiver_id} on suspicious blacklist"
            if triggered
            else "",
            evidence={"receiver_id": transaction.receiver_id},
            severity="high" if triggered else "low",
        )

    def _check_device_change_sensitive_action(
        self,
        transaction: Transaction,
        event_stream: EventStream,
        ref_time: datetime,
    ) -> LayerSignal:
        """Rule: new device within 24h of password reset or payee addition."""
        cutoff = ref_time - timedelta(hours=24)
        events = event_stream.query(account_id=transaction.sender_id, since=cutoff)

        has_device_change = any(e.event_type == EventType.DEVICE_CHANGE for e in events)
        has_sensitive = any(
            e.event_type in (EventType.PASSWORD_RESET, EventType.PAYEE_ADDED)
            for e in events
        )
        triggered = has_device_change and has_sensitive

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.85 if triggered else 0.0,
            explanation="New device within 24h of password reset or payee addition"
            if triggered
            else "",
            evidence={
                "device_change": has_device_change,
                "sensitive_action": has_sensitive,
            },
            severity="high" if triggered else "low",
        )

    def _check_balance_drain(
        self,
        transaction: Transaction,
        sender: AccountProfile,
    ) -> LayerSignal:
        """Rule: new_balance_sender == 0 after TRANSFER to first-time recipient."""
        if transaction.type != TransactionType.TRANSFER:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="",
                evidence={},
                severity="low",
            )

        is_first_time = transaction.receiver_id not in (sender.known_payees or [])
        balance_zeroed = transaction.new_balance_sender <= 0.01  # allow float tolerance

        triggered = is_first_time and balance_zeroed

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=0.92 if triggered else 0.0,
            explanation="Account drained to zero after transfer to first-time recipient"
            if triggered
            else "",
            evidence={
                "new_balance_sender": transaction.new_balance_sender,
                "receiver_id": transaction.receiver_id,
                "is_first_time": is_first_time,
            },
            severity="high" if triggered else "low",
        )

    def _check_layering_pattern(
        self,
        transaction: Transaction,
        event_stream: EventStream,
        ref_time: datetime,
    ) -> LayerSignal:
        """Rule: CASH_OUT zeroing account within 2 steps of matching inbound TRANSFER."""
        if transaction.type != TransactionType.CASH_OUT:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="",
                evidence={},
                severity="low",
            )

        if transaction.new_balance_sender > 0.01:
            return LayerSignal(
                layer_id=self.layer_id,
                layer_name=self.layer_name,
                triggered=False,
                confidence=0.0,
                explanation="",
                evidence={},
                severity="low",
            )

        # Look for recent inbound TRANSFER to this sender with matching amount
        cutoff = ref_time - timedelta(hours=48)
        all_events = event_stream.query(since=cutoff)

        txn_step = getattr(transaction, "step", 0)
        txn_amount = transaction.amount

        for ev in all_events:
            if not isinstance(ev.payload, dict):
                continue
            payload = ev.payload
            if payload.get("receiver_id") != transaction.sender_id:
                continue
            if payload.get("type") != TransactionType.TRANSFER.value:
                continue

            ev_step = payload.get("step", 0)
            ev_amount = payload.get("amount", 0)
            step_diff = abs(txn_step - ev_step)

            if step_diff <= LAYERING_STEP_WINDOW and abs(ev_amount - txn_amount) < 0.01:
                return LayerSignal(
                    layer_id=self.layer_id,
                    layer_name=self.layer_name,
                    triggered=True,
                    confidence=0.95,
                    explanation="CASH_OUT zeroes account within 2 steps of matching inbound TRANSFER (layering pattern)",
                    evidence={
                        "inbound_amount": ev_amount,
                        "outbound_amount": txn_amount,
                        "step_diff": step_diff,
                    },
                    severity="high",
                )

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=False,
            confidence=0.0,
            explanation="",
            evidence={},
            severity="low",
        )
