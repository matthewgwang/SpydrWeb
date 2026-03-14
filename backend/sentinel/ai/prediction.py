"""Step 2 — AI predicts exploitation risk and produces a TestPlan.

Uses the EXPLOITATION_ASSESSMENT_PROMPT to get the LLM's assessment
of which exploitation types are likely and which layers to prioritise.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.ai.prompts import EXPLOITATION_ASSESSMENT_PROMPT
from sentinel.models.layers import FraudType, TestPlan

if TYPE_CHECKING:
    from sentinel.ai.cache import ResponseCache
    from sentinel.ai.provider import LLMProvider
    from sentinel.models.account import AccountProfile, VulnerabilityScore
    from sentinel.models.events import Event
    from sentinel.models.transaction import Transaction

_TACTIC_TO_FRAUD_TYPE: dict[str, FraudType] = {
    "family_coercion": FraudType.ELDER_EXPLOITATION,
    "romance_scam": FraudType.ELDER_EXPLOITATION,
    "authority_impersonation": FraudType.ELDER_EXPLOITATION,
    "phone_coaching": FraudType.ELDER_EXPLOITATION,
    "account_takeover": FraudType.ACCOUNT_TAKEOVER,
    "mule_network": FraudType.MULE_NETWORK,
    "card_testing": FraudType.CARD_TESTING,
}


async def predict_exploitation_risk(
    sender_profile: AccountProfile,
    receiver_profile: AccountProfile,
    transaction: Transaction,
    recent_events: list[Event],
    vulnerability_score: VulnerabilityScore | None,
    provider: LLMProvider,
    cache: ResponseCache | None = None,
) -> TestPlan:
    """Ask the LLM to predict fraud types and layer priority."""
    vuln_score = vulnerability_score.score if vulnerability_score else 0.0
    vuln_factors = (
        ", ".join(f.factor for f in vulnerability_score.factors)
        if vulnerability_score and vulnerability_score.factors
        else "none"
    )

    events_text = "\n".join(
        f"  [{e.timestamp.isoformat()}] {e.event_type.value}: {e.payload}"
        for e in recent_events[-20:]
    ) or "  (none)"

    user_prompt = EXPLOITATION_ASSESSMENT_PROMPT.format(
        sender_profile=f"{sender_profile.name}, age {sender_profile.age}, {sender_profile.location}. {sender_profile.summary_text}",
        vulnerability_score=f"{vuln_score:.2f}",
        vulnerability_factors=vuln_factors,
        receiver_profile=f"{receiver_profile.name or receiver_profile.account_id}, age {receiver_profile.age or 'unknown'}, {receiver_profile.location or 'unknown'}",
        amount=transaction.amount,
        tx_type=transaction.type.value,
        channel=transaction.channel,
        old_balance_sender=transaction.old_balance_sender,
        new_balance_sender=transaction.new_balance_sender,
        is_new_payee=transaction.receiver_id not in sender_profile.known_payees,
        recent_events=events_text,
    )

    system_prompt = "You are a fraud risk assessment AI. Follow the instructions precisely."
    result = await provider.complete_json(system_prompt, user_prompt, cache=cache)

    if "error" in result:
        return _default_test_plan()

    try:
        exploitation_types = result.get("exploitation_types", [])
        fraud_types: list[FraudType] = []
        seen: set[FraudType] = set()
        for et in exploitation_types:
            type_name = et.get("type", "")
            mapped = _TACTIC_TO_FRAUD_TYPE.get(type_name)
            if mapped is None and type_name.upper() in FraudType.__members__:
                mapped = FraudType[type_name.upper()]
            if mapped is not None and mapped not in seen:
                fraud_types.append(mapped)
                seen.add(mapped)

        layer_priority = [
            lid for lid in result.get("priority_layers", [2, 3, 4]) if lid in (2, 3, 4)
        ]

        raw_weights = result.get("layer_weights", {})
        layer_weights = {int(k): float(v) for k, v in raw_weights.items()}

        return TestPlan(
            predicted_fraud_types=fraud_types or [FraudType.UNKNOWN],
            layer_priority=layer_priority or [2, 3, 4],
            layer_weights=layer_weights or {1: 0.2, 2: 0.3, 3: 0.2, 4: 0.3},
        )
    except Exception:
        return _default_test_plan()


def _default_test_plan() -> TestPlan:
    return TestPlan(
        predicted_fraud_types=[FraudType.UNKNOWN],
        layer_priority=[2, 3, 4],
        layer_weights={1: 0.2, 2: 0.3, 3: 0.2, 4: 0.3},
    )
