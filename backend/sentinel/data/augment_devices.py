"""Device/session event augmentation for PaySim accounts.

PaySim has no device info. This module generates realistic device events:
  - Normal accounts: 1-2 stable devices, consistent IPs
  - Fraud accounts: anomalous device changes before fraud transactions
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from sentinel.models.events import Event, EventType

if TYPE_CHECKING:
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream

# Device pools for generation
DEVICE_TYPES = [
    "iPhone_15", "iPhone_14", "iPhone_13", "Samsung_S24", "Samsung_S23",
    "Pixel_8", "Pixel_7", "MacBook_Pro", "Windows_Laptop", "iPad_Air",
]
CITIES = [
    "Toronto, ON", "Mississauga, ON", "Brampton, ON", "Markham, ON",
    "Scarborough, ON", "Vaughan, ON", "Ottawa, ON", "Hamilton, ON",
]

BASE_DATE = datetime(2026, 3, 1)


def _step_to_dt(step: int) -> datetime:
    return BASE_DATE + timedelta(hours=step)


def _make_device_id(account_id: str, idx: int) -> str:
    h = hashlib.md5(f"{account_id}_{idx}".encode()).hexdigest()[:8]
    return f"dev_{h}"


def _make_ip(account_id: str, idx: int) -> str:
    h = hashlib.md5(f"ip_{account_id}_{idx}".encode()).digest()
    return f"10.{h[0] % 256}.{h[1] % 256}.{h[2] % 256}"


def augment_devices(
    df: pd.DataFrame,
    event_stream: EventStream,
    graph: BrainGraph,
    seed: int = 42,
) -> dict:
    """Generate device events for all accounts in the DataFrame.

    For normal accounts: assign stable devices, generate periodic login events.
    For fraud accounts: inject anomalous device changes before fraud transactions.

    Returns summary stats.
    """
    rng = random.Random(seed)

    accounts = set(df["nameOrig"].unique())
    fraud_accounts = set(df[df["isFraud"] == 1]["nameOrig"].unique())

    device_map: dict[str, list[str]] = {}
    events_added = 0

    # Assign devices to every account
    for acc in accounts:
        n_devices = 1 if rng.random() < 0.6 else 2
        devices = [_make_device_id(acc, i) for i in range(n_devices)]
        device_map[acc] = devices

        primary_city = rng.choice(CITIES)

        # Link account → devices in graph
        for dev in devices:
            graph.add_node(dev, node_type="device", device_type=rng.choice(DEVICE_TYPES))
            graph.add_edge(acc, dev, edge_type="USES_DEVICE",
                           timestamp=_step_to_dt(0), location=primary_city)

    # For fraud accounts: inject suspicious device change before the fraud
    fraud_rows = df[df["isFraud"] == 1].sort_values("step")
    fraud_device_changes = 0

    for acc in fraud_accounts:
        acc_fraud = fraud_rows[fraud_rows["nameOrig"] == acc]
        if acc_fraud.empty:
            continue

        first_fraud_step = int(acc_fraud.iloc[0]["step"])

        # Create an attacker device (NOT in the account's normal set)
        attacker_dev = _make_device_id(f"attacker_{acc}", 0)
        attacker_ip = _make_ip(f"attacker_{acc}", 0)
        attacker_city = rng.choice([c for c in CITIES if c != CITIES[0]])

        graph.add_node(attacker_dev, node_type="device",
                       device_type=rng.choice(DEVICE_TYPES))

        # Device change event 1-24 hours before fraud
        hours_before = rng.randint(1, 24)
        change_step = max(0, first_fraud_step - hours_before)

        event_stream.append(Event(
            step=change_step,
            timestamp=_step_to_dt(change_step),
            event_type=EventType.DEVICE_CHANGE,
            account_id=acc,
            payload={
                "device_id": attacker_dev,
                "ip_address": attacker_ip,
                "location": attacker_city,
                "previous_device": device_map[acc][0],
            },
        ))
        graph.add_edge(acc, attacker_dev, edge_type="USES_DEVICE",
                       timestamp=_step_to_dt(change_step), location=attacker_city)
        events_added += 1
        fraud_device_changes += 1

    # For all accounts: generate periodic login events from their stable devices
    for acc in accounts:
        acc_txs = df[df["nameOrig"] == acc].sort_values("step")
        if acc_txs.empty:
            continue

        devices = device_map[acc]
        min_step = int(acc_txs["step"].min())
        max_step = int(acc_txs["step"].max())

        # ~1 login per day (every 24 steps), from a consistent device
        step = min_step
        while step <= max_step:
            dev = devices[0] if rng.random() < 0.85 else rng.choice(devices)
            event_stream.append(Event(
                step=step,
                timestamp=_step_to_dt(step),
                event_type=EventType.LOGIN,
                account_id=acc,
                payload={"device_id": dev, "ip_address": _make_ip(acc, 0)},
            ))
            events_added += 1
            step += rng.randint(18, 30)

    return {
        "accounts_augmented": len(accounts),
        "fraud_accounts": len(fraud_accounts),
        "fraud_device_changes": fraud_device_changes,
        "total_events_added": events_added,
        "device_map": device_map,
    }
