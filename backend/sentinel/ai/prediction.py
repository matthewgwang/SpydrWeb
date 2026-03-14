"""Step 2 — AI predicts exploitation risk and produces a TestPlan."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.models.layers import FraudType, TestPlan

if TYPE_CHECKING:
    from sentinel.accounts.vulnerability import VulnerabilityScore
    from sentinel.ai.cache import ResponseCache
    from sentinel.ai.provider import LLMProvider
    from sentinel.models.account import AccountProfile, VulnerabilityScore
    from sentinel.models.events import Event
    from sentinel.models.transaction import Transaction


async def predict_exploitation_risk(
    sender_profile: AccountProfile,
    receiver_profile: AccountProfile,
    transaction: Transaction,
    recent_events: list[Event],
    vulnerability_score,
    provider: LLMProvider,
    cache: ResponseCache | None = None,
) -> TestPlan:
    """Ask the LLM to predict fraud types and layer priority.

    Returns a TestPlan that guides the orchestrator on which layers to run
    and in what order.
    """
    system_prompt = (
        "You are a fraud-detection AI. Given a transaction and customer profiles, "
        "predict the most likely fraud types and which detection layers should run "
        "in priority order. Respond in JSON with keys: "
        "predicted_fraud_types (list of strings), layer_priority (list of ints 2-4), "
        "layer_weights (dict of layer_id -> weight 0.0-1.0)."
    )

    user_prompt = (
        f"Transaction: amount={transaction.amount}, type={transaction.type.value}, "
        f"sender={sender_profile.account_id}, receiver={receiver_profile.account_id}\n"
        f"Sender age: {sender_profile.age}, vulnerability: "
        f"{vulnerability_score.score if vulnerability_score else 'N/A'}\n"
        f"Recent events count: {len(recent_events)}\n"
        f"Receiver is {'known payee' if transaction.receiver_id in sender_profile.known_payees else 'NEW payee'}"
    )

    result = await provider.complete_json(system_prompt, user_prompt, cache=cache)

    if "error" in result:
        return _default_test_plan()

    try:
        fraud_types = [
            FraudType(ft) for ft in result.get("predicted_fraud_types", [])
            if ft in FraudType.__members__
        ]
        layer_priority = [
            lid for lid in result.get("layer_priority", [2, 3, 4])
            if lid in (2, 3, 4)
        ]
        layer_weights = {
            int(k): float(v)
            for k, v in result.get("layer_weights", {}).items()
        }

        return TestPlan(
            predicted_fraud_types=fraud_types or [FraudType.UNKNOWN],
            layer_priority=layer_priority or [2, 3, 4],
            layer_weights=layer_weights or {1: 0.2, 2: 0.3, 3: 0.25, 4: 0.25},
        )
    except Exception:
        return _default_test_plan()


def _default_test_plan() -> TestPlan:
    return TestPlan(
        predicted_fraud_types=[FraudType.UNKNOWN],
        layer_priority=[2, 3, 4],
        layer_weights={1: 0.2, 2: 0.3, 3: 0.25, 4: 0.25},
    )
