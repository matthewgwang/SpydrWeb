"""PaySim CSV loader — load, sample, and convert Kaggle PaySim data.

Expects the CSV at: datasets/paysim/PS_20174392719_1491204439457_log.csv
Download from: https://www.kaggle.com/datasets/ealaxi/paysim1

Columns: step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.models.transaction import Transaction, TransactionType

logger = logging.getLogger(__name__)

DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parent.parent / "datasets" / "paysim"
    / "PS_20174392719_1491204439457_log.csv"
)

PAYSIM_TYPE_MAP = {
    "CASH_IN": TransactionType.CASH_IN,
    "CASH_OUT": TransactionType.CASH_OUT,
    "DEBIT": TransactionType.DEBIT,
    "PAYMENT": TransactionType.PAYMENT,
    "TRANSFER": TransactionType.TRANSFER,
}


class PaySimLoader:
    """Load and sample the PaySim Kaggle dataset."""

    def __init__(self, csv_path: str | Path | None = None) -> None:
        self.csv_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH

    def is_available(self) -> bool:
        return self.csv_path.exists()

    def load_and_sample(
        self,
        csv_path: str | Path | None = None,
        n_transactions: int = 20_000,
        n_accounts: int = 500,
        min_fraud: int = 50,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Load PaySim CSV and sample a manageable subset.

        Returns dict with keys:
          - df: sampled DataFrame
          - transactions: list[Transaction]
          - fraud_df: DataFrame of isFraud=1 rows in sample
          - account_ids: sorted list of customer account IDs (C-prefix)
          - stats: summary statistics (includes total, fraud for build_all)
        """
        path = Path(csv_path) if csv_path else self.csv_path
        if not path.exists():
            raise FileNotFoundError(
                f"PaySim CSV not found at {path}. "
                "Download from https://www.kaggle.com/datasets/ealaxi/paysim1"
            )

        logger.info("Loading PaySim CSV from %s ...", path)
        df = pd.read_csv(path)
        logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))

        rng = np.random.default_rng(seed)

        # Separate fraud and non-fraud
        fraud_df = df[df["isFraud"] == 1]
        clean_df = df[df["isFraud"] == 0]

        # Sample fraud rows (take all if fewer than min_fraud)
        n_fraud = min(len(fraud_df), max(min_fraud, 50))
        fraud_sample = fraud_df.sample(n=n_fraud, random_state=seed)

        # Collect accounts involved in fraud
        fraud_accounts = set(fraud_sample["nameOrig"]) | set(fraud_sample["nameDest"])

        # Sample additional clean accounts to reach n_accounts
        all_clean_accounts = set(clean_df["nameOrig"].unique())
        extra_accounts_needed = max(0, n_accounts - len(fraud_accounts))
        available = list(all_clean_accounts - fraud_accounts)
        rng.shuffle(available)
        sampled_accounts = fraud_accounts | set(available[:extra_accounts_needed])

        # Get all transactions for sampled accounts
        mask = df["nameOrig"].isin(sampled_accounts) | df["nameDest"].isin(sampled_accounts)
        account_df = df[mask]

        # If too many, subsample to n_transactions (keeping all fraud)
        if len(account_df) > n_transactions:
            fraud_in_account = account_df[account_df["isFraud"] == 1]
            clean_in_account = account_df[account_df["isFraud"] == 0]
            n_clean = n_transactions - len(fraud_in_account)
            clean_sample = clean_in_account.sample(
                n=min(n_clean, len(clean_in_account)), random_state=seed
            )
            account_df = pd.concat([fraud_in_account, clean_sample])

        account_df = account_df.sort_values("step").reset_index(drop=True)

        # Convert to Transaction objects
        transactions = self._df_to_transactions(account_df)

        # Recompute fraud_df for the sample
        sampled_fraud = account_df[account_df["isFraud"] == 1]

        # Extract account_ids (C-prefix customer accounts) for build_all
        account_ids = sorted(
            {aid for aid in sampled_accounts if str(aid).startswith("C")}
        )

        stats = {
            "total_rows_in_csv": len(df),
            "sampled_rows": len(account_df),
            "sampled_accounts": len(sampled_accounts),
            "fraud_rows": len(sampled_fraud),
            "clean_rows": len(account_df) - len(sampled_fraud),
            "total": len(account_df),
            "fraud": len(sampled_fraud),
            "type_distribution": account_df["type"].value_counts().to_dict(),
            "fraud_type_distribution": sampled_fraud["type"].value_counts().to_dict(),
        }

        logger.info(
            "Sampled %d transactions (%d fraud) across %d accounts",
            stats["sampled_rows"], stats["fraud_rows"], stats["sampled_accounts"],
        )

        return {
            "df": account_df,
            "transactions": transactions,
            "fraud_df": sampled_fraud,
            "account_ids": account_ids,
            "stats": stats,
        }

    def load_full_stats(self) -> dict[str, Any]:
        """Load the full CSV and compute statistical distributions (for calibration).

        Does NOT load all rows into memory as Transaction objects — just computes
        aggregate stats from the DataFrame.
        """
        if not self.is_available():
            raise FileNotFoundError(f"PaySim CSV not found at {self.csv_path}")

        df = pd.read_csv(self.csv_path)

        stats: dict[str, Any] = {}

        for tx_type in ["TRANSFER", "CASH_OUT", "PAYMENT", "CASH_IN", "DEBIT"]:
            subset = df[df["type"] == tx_type]
            clean = subset[subset["isFraud"] == 0]
            fraud = subset[subset["isFraud"] == 1]

            if len(clean) > 0:
                stats[tx_type] = {
                    "count": int(len(subset)),
                    "fraud_count": int(len(fraud)),
                    "fraud_rate": float(len(fraud) / len(subset)) if len(subset) > 0 else 0,
                    "amount_mean": float(clean["amount"].mean()),
                    "amount_std": float(clean["amount"].std()),
                    "amount_median": float(clean["amount"].median()),
                    "amount_p95": float(clean["amount"].quantile(0.95)),
                    "amount_p99": float(clean["amount"].quantile(0.99)),
                    "amount_max": float(clean["amount"].max()),
                    "balance_drain_ratio_mean": float(
                        (clean["oldbalanceOrg"] - clean["newbalanceOrig"])
                        .div(clean["oldbalanceOrg"].replace(0, np.nan))
                        .dropna()
                        .mean()
                    ),
                }

        # Velocity: transactions per account per step (hour)
        velocity = df.groupby(["nameOrig", "step"]).size()
        stats["velocity"] = {
            "mean_per_hour": float(velocity.mean()),
            "p95_per_hour": float(velocity.quantile(0.95)),
            "p99_per_hour": float(velocity.quantile(0.99)),
            "max_per_hour": int(velocity.max()),
        }

        # Step distribution (hour of day patterns)
        stats["step_distribution"] = {
            "total_steps": int(df["step"].max()),
            "transactions_per_step_mean": float(df.groupby("step").size().mean()),
        }

        return stats

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
    def _df_to_transactions(df: pd.DataFrame) -> list[Transaction]:
        base_time = datetime(2026, 1, 1, tzinfo=UTC)
        transactions = []
        for _, row in df.iterrows():
            step = int(row["step"])
            ts = base_time + timedelta(hours=step)
            tx_type = PAYSIM_TYPE_MAP.get(row["type"], TransactionType.PAYMENT)
            tx = Transaction(
                step=step,
                timestamp=ts,
                type=tx_type,
                amount=float(row["amount"]),
                sender_id=str(row["nameOrig"]),
                receiver_id=str(row["nameDest"]),
                old_balance_sender=float(row["oldbalanceOrg"]),
                new_balance_sender=float(row["newbalanceOrig"]),
                old_balance_receiver=float(row["oldbalanceDest"]),
                new_balance_receiver=float(row["newbalanceDest"]),
                is_fraud=bool(row["isFraud"]),
                channel="mobile",
                description=f"PaySim {row['type']}",
            )
            transactions.append(tx)
        return transactions
