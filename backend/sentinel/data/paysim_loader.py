"""PaySim CSV loader — samples a working subset for SENTINEL demos.

Expects the Kaggle PaySim CSV (ealaxi/paysim1) with columns:
step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
"""

from __future__ import annotations

import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sentinel.models.transaction import Transaction, TransactionType

_TYPE_MAP = {
    "CASH_IN": TransactionType.CASH_IN,
    "CASH_OUT": TransactionType.CASH_OUT,
    "DEBIT": TransactionType.DEBIT,
    "PAYMENT": TransactionType.PAYMENT,
    "TRANSFER": TransactionType.TRANSFER,
}

_PAYSIM_DEFAULT_PATH = Path("sentinel/datasets/paysim")


class PaySimLoader:
    """Load and sample PaySim CSV for demo use."""

    def __init__(self, csv_path: str | Path | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else None

    def load_and_sample(
        self,
        csv_path: str | Path | None = None,
        n_transactions: int = 20_000,
        n_accounts: int = 500,
        min_fraud: int = 50,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Load PaySim CSV and return a sampled subset.

        Returns dict with keys: transactions, fraud_transactions,
        account_ids, merchant_ids, stats.
        """
        path = Path(csv_path) if csv_path else self.csv_path
        if path is None or not path.exists():
            raise FileNotFoundError(
                f"PaySim CSV not found at {path}. "
                "Download from https://www.kaggle.com/datasets/ealaxi/paysim1 "
                "and place the CSV in sentinel/datasets/paysim/"
            )

        rng = random.Random(seed)
        rows: list[dict] = []
        fraud_rows: list[dict] = []

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                is_fraud = row.get("isFraud", "0") == "1"
                if is_fraud:
                    fraud_rows.append(row)
                else:
                    rows.append(row)

        if len(fraud_rows) < min_fraud:
            sampled_fraud = fraud_rows
        else:
            sampled_fraud = rng.sample(fraud_rows, min_fraud)

        fraud_accounts = set()
        for r in sampled_fraud:
            fraud_accounts.add(r["nameOrig"])
            fraud_accounts.add(r["nameDest"])

        remaining_budget = n_transactions - len(sampled_fraud)
        if remaining_budget > 0:
            related = [r for r in rows if r["nameOrig"] in fraud_accounts or r["nameDest"] in fraud_accounts]
            unrelated = [r for r in rows if r["nameOrig"] not in fraud_accounts and r["nameDest"] not in fraud_accounts]

            n_related = min(len(related), remaining_budget // 3)
            n_unrelated = min(len(unrelated), remaining_budget - n_related)

            sampled_normal = rng.sample(related, n_related) + rng.sample(unrelated, n_unrelated)
        else:
            sampled_normal = []

        all_sampled = sampled_fraud + sampled_normal
        all_sampled.sort(key=lambda r: int(r["step"]))

        account_ids: set[str] = set()
        merchant_ids: set[str] = set()
        for r in all_sampled:
            orig, dest = r["nameOrig"], r["nameDest"]
            if orig.startswith("C"):
                account_ids.add(orig)
            if dest.startswith("C"):
                account_ids.add(dest)
            if dest.startswith("M"):
                merchant_ids.add(dest)

        if len(account_ids) > n_accounts:
            keep = set(rng.sample(sorted(account_ids), n_accounts))
            keep.update(fraud_accounts & account_ids)
            all_sampled = [r for r in all_sampled if r["nameOrig"] in keep or r["nameDest"] in keep]
            account_ids &= keep

        transactions = [self._row_to_transaction(r) for r in all_sampled]
        fraud_txns = [t for t in transactions if t.is_fraud]

        return {
            "transactions": transactions,
            "fraud_transactions": fraud_txns,
            "account_ids": sorted(account_ids),
            "merchant_ids": sorted(merchant_ids),
            "stats": {
                "total": len(transactions),
                "fraud": len(fraud_txns),
                "accounts": len(account_ids),
                "merchants": len(merchant_ids),
            },
        }

    def find_scenario_candidates(self, transactions: list[Transaction]) -> dict[str, list[Transaction]]:
        """Identify PaySim fraud patterns that map to our 4 demo scenarios.

        Returns dict keyed by scenario name with lists of candidate
        transactions suitable for each.
        """
        fraud_txns = [t for t in transactions if t.is_fraud]

        large_transfers = [
            t for t in fraud_txns
            if t.type == TransactionType.TRANSFER and t.amount > 2000
        ]
        cash_outs = [
            t for t in fraud_txns
            if t.type == TransactionType.CASH_OUT
        ]
        rapid_senders: dict[str, list[Transaction]] = {}
        for t in fraud_txns:
            rapid_senders.setdefault(t.sender_id, []).append(t)
        rapid_burst = [
            txns for txns in rapid_senders.values() if len(txns) >= 3
        ]
        small_merchant: dict[str, list[Transaction]] = {}
        for t in fraud_txns:
            if t.amount < 20 and t.receiver_id.startswith("M"):
                small_merchant.setdefault(t.receiver_id, []).append(t)
        card_test_merchants = [
            txns for txns in small_merchant.values() if len(txns) >= 5
        ]

        return {
            "elder_exploitation": large_transfers[:10],
            "account_takeover": cash_outs[:10],
            "mule_network": [t for batch in rapid_burst[:3] for t in batch],
            "card_testing": [t for batch in card_test_merchants[:3] for t in batch],
        }

    @staticmethod
    def _row_to_transaction(row: dict) -> Transaction:
        step = int(row["step"])
        base_time = datetime(2026, 1, 1, tzinfo=UTC)
        ts = base_time + timedelta(hours=step)

        tx_type = _TYPE_MAP.get(row["type"], TransactionType.PAYMENT)

        return Transaction(
            step=step,
            timestamp=ts,
            type=tx_type,
            amount=float(row["amount"]),
            sender_id=row["nameOrig"],
            receiver_id=row["nameDest"],
            old_balance_sender=float(row.get("oldbalanceOrg", 0)),
            new_balance_sender=float(row.get("newbalanceOrig", 0)),
            old_balance_receiver=float(row.get("oldbalanceDest", 0)),
            new_balance_receiver=float(row.get("newbalanceDest", 0)),
            is_fraud=row.get("isFraud", "0") == "1",
            channel="mobile",
            description=f"PaySim {row['type']}",
        )
