"""Master build script — runs all PaySim data generation in order.

Usage:
    python -m sentinel.data.build_all --csv path/to/paysim.csv

Outputs augmented data to sentinel/processed/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_DIR = Path("sentinel/processed")


def build_all(
    paysim_csv: str | Path | None = None,
    output_dir: str | Path | None = None,
    n_transactions: int = 20_000,
    n_accounts: int = 500,
    seed: int = 42,
) -> dict[str, Any]:
    """Run the full PaySim data pipeline.

    Steps:
    1. Load and sample PaySim CSV
    2. Generate account metadata (augment_accounts)
    3. Generate communication events (augment_comms)
    4. Write all outputs to processed/ directory

    Returns summary statistics.
    """
    out = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    out.mkdir(parents=True, exist_ok=True)

    from sentinel.data.paysim_loader import PaySimLoader

    loader = PaySimLoader()
    logger.info("Loading PaySim CSV from %s", paysim_csv)
    sample = loader.load_and_sample(
        csv_path=paysim_csv,
        n_transactions=n_transactions,
        n_accounts=n_accounts,
        seed=seed,
    )
    logger.info("Sampled %d transactions (%d fraud)", sample["stats"]["total"], sample["stats"]["fraud"])

    transactions_out = [
        {
            "id": t.id,
            "step": t.step,
            "timestamp": t.timestamp.isoformat(),
            "type": t.type.value,
            "amount": t.amount,
            "sender_id": t.sender_id,
            "receiver_id": t.receiver_id,
            "old_balance_sender": t.old_balance_sender,
            "new_balance_sender": t.new_balance_sender,
            "is_fraud": t.is_fraud,
        }
        for t in sample["transactions"]
    ]
    _write_json(out / "transactions.json", transactions_out)

    from sentinel.data.augment_accounts import augment_accounts

    logger.info("Generating account metadata for %d accounts", len(sample["account_ids"]))
    personas = augment_accounts(sample["account_ids"], seed=seed)
    _write_json(out / "accounts.json", personas)

    from sentinel.data.augment_comms import generate_normal_comms

    logger.info("Generating communication events")
    all_comms: list[dict] = []
    for persona in personas[:100]:
        comms = generate_normal_comms(persona, days=90, seed=seed)
        for event in comms:
            all_comms.append({
                "id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type.value,
                "account_id": event.account_id,
                "payload": event.payload,
            })
    _write_json(out / "communications.json", all_comms)

    scenarios = loader.find_scenario_candidates(sample["transactions"])
    scenarios_out = {
        name: [{"id": t.id, "amount": t.amount, "sender_id": t.sender_id} for t in txns]
        for name, txns in scenarios.items()
    }
    _write_json(out / "scenarios.json", scenarios_out)

    summary = {
        "transactions": sample["stats"]["total"],
        "fraud_transactions": sample["stats"]["fraud"],
        "accounts": len(personas),
        "communications": len(all_comms),
        "scenario_candidates": {k: len(v) for k, v in scenarios.items()},
        "output_dir": str(out),
    }

    _write_json(out / "build_summary.json", summary)
    logger.info("Build complete: %s", summary)
    return summary


def _write_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Wrote %s", path)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Build augmented PaySim data")
    parser.add_argument("--csv", required=True, help="Path to PaySim CSV file")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--n-transactions", type=int, default=20_000)
    parser.add_argument("--n-accounts", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    build_all(
        paysim_csv=args.csv,
        output_dir=args.output,
        n_transactions=args.n_transactions,
        n_accounts=args.n_accounts,
        seed=args.seed,
    )
