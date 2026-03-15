"""Normal transaction history generator.

Creates realistic transaction history for each persona so that
baselines can be computed before the fraud scenario is injected.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from app.models.events import Event, EventType
from app.models.transaction import Transaction, TransactionType


def generate_normal_history(
    persona: dict,
    days: int = 90,
    start_date: datetime | None = None,
) -> tuple[list[Transaction], list[Event]]:
    """Generate days of normal transaction + event history for a persona.

    Returns (transactions, events).
    """
    rng = random.Random(hash(persona["account_id"]))
    behavior = persona.get("behavior", {})
    account_id = persona["account_id"]

    avg_amount = behavior.get("avg_amount", 50.0)
    std_amount = behavior.get("std_amount", 25.0)
    daily_freq = behavior.get("daily_frequency", 1.0)
    typical_hours = behavior.get("typical_hours", [10, 14])
    merchants = behavior.get("typical_merchants", ["Store"])
    channel_weights = behavior.get("typical_channels", {"online": 100})
    known_payees = behavior.get("known_payees", [])
    balance_check_freq = behavior.get("balance_check_frequency", 0.0)
    devices = behavior.get("devices", ["device_default"])

    base = start_date or (datetime.now(UTC) - timedelta(days=days))
    transactions: list[Transaction] = []
    events: list[Event] = []
    balance = rng.uniform(3000, 15000)
    step = 0

    channels = list(channel_weights.keys())
    channel_probs = [channel_weights[c] for c in channels]
    total_prob = sum(channel_probs)
    channel_probs = [p / total_prob for p in channel_probs]

    for day in range(days):
        current_date = base + timedelta(days=day)
        step_base = day * 24

        # Balance checks
        if balance_check_freq > 0 and rng.random() < balance_check_freq:
            check_hour = rng.choice(typical_hours[:2]) if typical_hours else 9
            events.append(Event(
                timestamp=current_date.replace(hour=check_hour, minute=rng.randint(0, 59)),
                step=step_base + check_hour,
                event_type=EventType.BALANCE_CHECK,
                account_id=account_id,
                payload={"device_id": rng.choice(devices)},
            ))

        # Login events
        if rng.random() < 0.7:
            login_hour = rng.choice(typical_hours) if typical_hours else 10
            events.append(Event(
                timestamp=current_date.replace(hour=login_hour, minute=rng.randint(0, 59)),
                step=step_base + login_hour,
                event_type=EventType.LOGIN,
                account_id=account_id,
                payload={"device_id": rng.choice(devices)},
            ))

        # Transactions
        n_txns = max(0, int(rng.gauss(daily_freq, daily_freq * 0.3)))
        for _ in range(n_txns):
            amount = max(1.0, rng.gauss(avg_amount, std_amount))
            hour = rng.choice(typical_hours) if typical_hours else rng.randint(8, 20)
            minute = rng.randint(0, 59)
            ts = current_date.replace(hour=hour, minute=minute)
            step_val = step_base + hour

            channel = rng.choices(channels, weights=channel_probs, k=1)[0]
            merchant = rng.choice(merchants) if merchants else "Merchant"

            receiver = rng.choice(known_payees) if known_payees and rng.random() < 0.3 else merchant

            old_balance = balance
            balance -= amount
            if balance < 500:
                balance += rng.uniform(1000, 5000)

            tx = Transaction(
                step=step_val,
                timestamp=ts,
                type=TransactionType.PAYMENT,
                amount=round(amount, 2),
                sender_id=account_id,
                receiver_id=receiver,
                old_balance_sender=round(old_balance, 2),
                new_balance_sender=round(balance, 2),
                old_balance_receiver=0.0,
                new_balance_receiver=0.0,
                channel=channel,
                description=merchant,
            )
            transactions.append(tx)

            events.append(Event(
                timestamp=ts,
                step=step_val,
                event_type=EventType.TRANSACTION,
                account_id=account_id,
                payload={**tx.model_dump(), "merchant_category": merchant},
            ))

    transactions.sort(key=lambda t: t.timestamp)
    events.sort(key=lambda e: e.timestamp)
    return transactions, events
