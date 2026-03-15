"""Communication augmentation — generates chat transcripts and branch notes.

Produces realistic customer support interactions for each persona so
Layer 4 (Comprehension) has communication data to analyze.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from app.models.events import Event, EventType

_NORMAL_CHATS_YOUNG = [
    "hey can you check if my e-transfer went through? sent it like an hour ago",
    "my card got declined at the store but I have money in my account??",
    "want to set up auto-pay for my rent, how do I do that",
    "can you increase my daily etransfer limit? need to pay my roommate back",
    "is there an outage? the app won't load for me rn",
]

_NORMAL_CHATS_MIDDLE = [
    "Hi, I'd like to set up a recurring payment for daycare. Can you walk me through it?",
    "I noticed a charge on my account that I don't recognize — $47.50 from 'TKT Services'.",
    "Can I get a copy of my last 3 months of statements for my mortgage application?",
    "I need to update my address. We just moved to a new house.",
    "What's the interest rate on your savings accounts right now?",
]

_NORMAL_CHATS_SENIOR = [
    "Hi, what's my balance please?",
    "I think my card isn't working at the grocery store",
    "Can you help me with my phone bill payment?",
    "I'd like to check on my account please",
    "When does my pension come in this month?",
    "Hello, I'm having trouble with the app. It keeps asking me for a password.",
    "Can someone help me understand this charge on my statement?",
]

_NORMAL_BRANCH_NOTES = [
    "Customer visited to deposit cheque. Pleasant interaction, no concerns.",
    "Customer requested printed statement for tax filing. Assisted at counter.",
    "Customer asked about GIC rates. Referred to advisor.",
    "Customer renewed debit card. Verified identity with photo ID.",
]

_FRAUD_COACHED_CHAT = (
    "Hi there. My grandson is helping me set up online banking. I need to add a new "
    "payee and I'd like to know what my e-transfer limit is. Can you walk me through "
    "how to initiate a wire transfer to a beneficiary account? I want to make sure "
    "the funds are transferred promptly."
)

_FRAUD_ROMANCE_CHAT = (
    "I need to send money to someone overseas. It's for a friend who is having "
    "medical issues. Please don't ask too many questions, this is urgent and I "
    "know what I'm doing. Can you just tell me how to do an international wire?"
)

_FRAUD_AUTHORITY_CHAT = (
    "Hello, I received a call from your fraud department saying my account has "
    "been compromised. They told me to transfer my savings to a safe account "
    "immediately. Can you help me do that? The officer said time is critical."
)

_FRAUD_BRANCH_COACHED = (
    "Customer accompanied by younger male who identified himself as her grandson. "
    "He was answering most questions and guiding the customer through the interaction. "
    "Customer seemed confused but agreeable."
)


def generate_normal_comms(
    persona: dict,
    days: int = 90,
    start_date: datetime | None = None,
    seed: int | None = None,
) -> list[Event]:
    """Generate normal communication events for a persona.

    Returns a list of Events (SUPPORT_CHAT, BRANCH_VISIT) that
    represent the persona's typical interaction history.
    """
    rng = random.Random(seed or hash(persona["account_id"]))
    account_id = persona["account_id"]
    age = persona.get("age", 40)
    behavior = persona.get("behavior", {})
    freq = behavior.get("support_interaction_frequency", 0.1)
    devices = behavior.get("devices", ["device_default"])

    base = start_date or (datetime.now(UTC) - timedelta(days=days))
    events: list[Event] = []

    if age >= 60:
        chat_pool = _NORMAL_CHATS_SENIOR
    elif age >= 30:
        chat_pool = _NORMAL_CHATS_MIDDLE
    else:
        chat_pool = _NORMAL_CHATS_YOUNG

    channels = behavior.get("typical_channels", {})
    has_branch = channels.get("branch", 0) > 0

    for day in range(days):
        current_date = base + timedelta(days=day)

        if rng.random() < freq:
            hour = rng.randint(9, 17)
            ts = current_date.replace(hour=hour, minute=rng.randint(0, 59))
            step = day * 24 + hour

            if has_branch and rng.random() < 0.3:
                events.append(Event(
                    timestamp=ts,
                    step=step,
                    event_type=EventType.BRANCH_VISIT,
                    account_id=account_id,
                    payload={
                        "branch": _random_branch(rng, persona.get("location", "")),
                        "note": rng.choice(_NORMAL_BRANCH_NOTES),
                    },
                ))
            else:
                events.append(Event(
                    timestamp=ts,
                    step=step,
                    event_type=EventType.SUPPORT_CHAT,
                    account_id=account_id,
                    payload={
                        "channel": "webchat",
                        "device_id": rng.choice(devices),
                        "content": rng.choice(chat_pool),
                        "session_duration_minutes": rng.randint(2, 15),
                    },
                ))

    events.sort(key=lambda e: e.timestamp)
    return events


def generate_fraud_comms(
    persona: dict,
    scenario: str,
    fraud_step: int,
    base_time: datetime | None = None,
) -> list[Event]:
    """Generate communication events that indicate fraud/coaching.

    These are the suspicious interactions that Layer 4 should flag.

    Args:
        persona: Target victim persona dict.
        scenario: One of 'elder_exploitation', 'romance_scam',
                  'authority_impersonation', 'phone_coaching'.
        fraud_step: The step number of the fraud transaction.
        base_time: Base datetime for step 0.
    """
    account_id = persona["account_id"]
    base = base_time or datetime(2026, 1, 1, tzinfo=UTC)

    events: list[Event] = []

    if scenario == "elder_exploitation":
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 14),
            step=fraud_step - 14,
            event_type=EventType.BRANCH_VISIT,
            account_id=account_id,
            payload={
                "branch": _random_branch(None, persona.get("location", "")),
                "note": _FRAUD_BRANCH_COACHED,
                "staff_member": "Jennifer Walsh",
            },
        ))
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 2),
            step=fraud_step - 2,
            event_type=EventType.SUPPORT_CHAT,
            account_id=account_id,
            payload={
                "channel": "webchat",
                "device_id": "dev_external_unknown",
                "content": _FRAUD_COACHED_CHAT,
                "session_duration_minutes": 12,
                "response_pattern": "slow_then_fast",
            },
        ))

    elif scenario == "romance_scam":
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 4),
            step=fraud_step - 4,
            event_type=EventType.SUPPORT_CHAT,
            account_id=account_id,
            payload={
                "channel": "webchat",
                "device_id": persona.get("behavior", {}).get("devices", ["device_default"])[0],
                "content": _FRAUD_ROMANCE_CHAT,
                "session_duration_minutes": 8,
            },
        ))

    elif scenario == "authority_impersonation":
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 1),
            step=fraud_step - 1,
            event_type=EventType.PHONE_CALL,
            account_id=account_id,
            payload={
                "direction": "inbound",
                "caller_id": "BLOCKED",
                "duration_minutes": 22,
                "note": "Incoming call from unknown number just before transaction",
            },
        ))
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 0.5),
            step=fraud_step,
            event_type=EventType.SUPPORT_CHAT,
            account_id=account_id,
            payload={
                "channel": "webchat",
                "content": _FRAUD_AUTHORITY_CHAT,
                "session_duration_minutes": 5,
                "response_pattern": "fast_urgent",
            },
        ))

    elif scenario == "phone_coaching":
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 1),
            step=fraud_step - 1,
            event_type=EventType.PHONE_CALL,
            account_id=account_id,
            payload={
                "direction": "inbound",
                "duration_minutes": 45,
                "note": "Extended call overlapping with online banking session",
            },
        ))
        events.append(Event(
            timestamp=base + timedelta(hours=fraud_step - 0.5),
            step=fraud_step,
            event_type=EventType.SUPPORT_CHAT,
            account_id=account_id,
            payload={
                "channel": "webchat",
                "device_id": "dev_external_unknown",
                "content": _FRAUD_COACHED_CHAT,
                "session_duration_minutes": 18,
                "response_pattern": "slow_then_fast",
            },
        ))

    return events


def _random_branch(rng: random.Random | None, location: str) -> str:
    city = location.split(",")[0].strip() if location else "Toronto"
    branches = [
        f"TD {city} Town Centre",
        f"TD {city} Main Street",
        f"TD {city} South",
    ]
    if rng:
        return rng.choice(branches)
    return branches[0]
