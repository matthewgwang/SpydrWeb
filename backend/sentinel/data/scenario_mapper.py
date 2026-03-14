"""Map PaySim isFraud=1 patterns to SENTINEL demo scenarios.

Analyzes fraud transaction clusters and classifies them:
  - elder_exploitation: single large transfer from low-activity sender
  - account_takeover:   rapid drain sequence (multiple transfers, same sender)
  - mule_network:       fan-in pattern (many senders → one receiver)
  - card_testing:       burst of small payments to one merchant
"""

from __future__ import annotations

import logging
from collections import defaultdict

import pandas as pd

logger = logging.getLogger(__name__)


def map_fraud_to_scenarios(fraud_df: pd.DataFrame, full_df: pd.DataFrame) -> dict:
    """Classify PaySim fraud rows into our 4 demo scenarios.

    Args:
        fraud_df: DataFrame of isFraud=1 rows.
        full_df: Full sampled DataFrame (for sender history context).

    Returns dict mapping scenario_name → list of fraud row indices.
    """
    scenarios: dict[str, list[int]] = {
        "elder_exploitation": [],
        "account_takeover": [],
        "mule_network": [],
        "card_testing": [],
        "unclassified": [],
    }

    if fraud_df.empty:
        return scenarios

    # Pre-compute per-sender stats from the full dataset
    sender_tx_counts = full_df.groupby("nameOrig").size()
    sender_avg_amounts = full_df.groupby("nameOrig")["amount"].mean()

    # Group fraud by sender to detect drain sequences
    fraud_by_sender = defaultdict(list)
    for idx, row in fraud_df.iterrows():
        fraud_by_sender[row["nameOrig"]].append((idx, row))

    # Group fraud by receiver to detect fan-in
    fraud_by_receiver = defaultdict(list)
    for idx, row in fraud_df.iterrows():
        fraud_by_receiver[row["nameDest"]].append((idx, row))

    classified_indices = set()

    # Pattern 1: Mule network — receiver gets from 3+ different senders
    for receiver, entries in fraud_by_receiver.items():
        unique_senders = {row["nameOrig"] for _, row in entries}
        if len(unique_senders) >= 3:
            for idx, _ in entries:
                scenarios["mule_network"].append(idx)
                classified_indices.add(idx)

    # Pattern 2: Card testing — small payments (<100) to merchant (M-prefix)
    # Must run BEFORE account_takeover since burst of small txs would also match ATO
    for sender, entries in fraud_by_sender.items():
        unclassified_entries = [(i, r) for i, r in entries if i not in classified_indices]
        merchant_entries = [
            (i, r) for i, r in unclassified_entries
            if str(r["nameDest"]).startswith("M") and r["amount"] < 100
        ]
        if len(merchant_entries) >= 3:
            for idx, _ in merchant_entries:
                scenarios["card_testing"].append(idx)
                classified_indices.add(idx)

    # Pattern 3: Account takeover — same sender, 2+ fraud transfers in short window
    for sender, entries in fraud_by_sender.items():
        if len(entries) < 2:
            continue
        indices = [idx for idx, _ in entries]
        if any(i in classified_indices for i in indices):
            continue

        steps = sorted(row["step"] for _, row in entries)
        window = steps[-1] - steps[0]
        if window <= 48:  # within 48 hours
            for idx, _ in entries:
                scenarios["account_takeover"].append(idx)
                classified_indices.add(idx)

    # Pattern 4: Elder exploitation — single large transfer, sender has low activity
    for sender, entries in fraud_by_sender.items():
        unclassified_entries = [(i, r) for i, r in entries if i not in classified_indices]
        for idx, row in unclassified_entries:
            sender_count = sender_tx_counts.get(sender, 0)
            sender_avg = sender_avg_amounts.get(sender, 0)
            amount = row["amount"]

            # Low activity account + transfer much larger than average
            is_low_activity = sender_count < 20
            is_large_relative = amount > sender_avg * 5 if sender_avg > 0 else amount > 2000
            is_transfer = row["type"] == "TRANSFER"

            if is_transfer and (is_low_activity or is_large_relative):
                scenarios["elder_exploitation"].append(idx)
                classified_indices.add(idx)

    # Everything else
    for idx in fraud_df.index:
        if idx not in classified_indices:
            scenarios["unclassified"].append(idx)

    summary = {k: len(v) for k, v in scenarios.items()}
    logger.info("Scenario mapping: %s", summary)

    return scenarios


def get_scenario_summary(scenarios: dict, fraud_df: pd.DataFrame) -> dict:
    """Return human-readable summary of mapped scenarios."""
    summary = {}
    for name, indices in scenarios.items():
        if not indices:
            summary[name] = {"count": 0, "total_amount": 0, "examples": []}
            continue

        rows = fraud_df.loc[fraud_df.index.isin(indices)]
        summary[name] = {
            "count": len(indices),
            "total_amount": float(rows["amount"].sum()),
            "avg_amount": float(rows["amount"].mean()),
            "unique_senders": int(rows["nameOrig"].nunique()),
            "unique_receivers": int(rows["nameDest"].nunique()),
            "examples": [
                {
                    "sender": row["nameOrig"],
                    "receiver": row["nameDest"],
                    "amount": float(row["amount"]),
                    "step": int(row["step"]),
                    "type": row["type"],
                }
                for _, row in rows.head(3).iterrows()
            ],
        }
    return summary
