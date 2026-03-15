"""Fraud scenario injectors — add realistic fraud events to EventStream and BrainGraph.

Each function injects a complete fraud scenario (events + graph edges) and returns
the fraud transaction(s) for the orchestrator to process.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.models.events import Event, EventType
from app.models.transaction import Transaction, TransactionType

if TYPE_CHECKING:
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream

# Base date for step-to-datetime conversion (1 step = 1 hour)
BASE_DATE = datetime(2026, 3, 1, tzinfo=UTC)


def step_to_datetime(step: int) -> datetime:
    """Convert PaySim step (1 step = 1 hour) to datetime (UTC-aware)."""
    return BASE_DATE + timedelta(hours=step)


# Default target for elder exploitation (used when no persona provided)
MARGARET_CHEN = {
    "account_id": "Margaret",
    "name": "Margaret Chen",
    "age": 74,
    "location": "Scarborough, ON",
    "behavior": {
        "devices": ["dev_margaret_iphone"],
        "known_payees": ["Bell Canada Auto-Pay", "Grocery", "Pharmacy", "Hydro"],
    },
}

# Jason Chen — the exploiter (receives from Margaret and other victims)
JASON_ACCOUNT_ID = "C840083671"

# Robert Williams — another elderly victim Jason exploited (for fan-in signal)
ROBERT_ACCOUNT_ID = "C1666544295"

# Account takeover — default victim and mule
SARAH_MITCHELL = {
    "account_id": "Sarah",
    "name": "Sarah Mitchell",
    "age": 42,
    "location": "Toronto, ON",
    "behavior": {
        "devices": ["dev_sarah_macbook", "dev_sarah_iphone"],
        "known_payees": ["Rent", "Utilities", "Netflix", "Grocery"],
    },
}

ATO_MULE_ACCOUNT_ID = "C_ATO_MULE"

# Mule network — 5 mule accounts sharing one device
MULE_ACCOUNT_IDS = ["C_MULE_1", "C_MULE_2", "C_MULE_3", "C_MULE_4", "C_MULE_5"]
MULE_SHARED_DEVICE = "dev_mule_assembly"

# Card testing — merchant and tester account
CARD_TEST_MERCHANT = "M_CARD_TEST"
CARD_TESTER_ACCOUNT = "C_CARD_TESTER"


def inject_elder_exploitation(
    event_stream: EventStream,
    graph: BrainGraph,
    target_persona: dict | None = None,
    fraud_step: int = 342,
) -> Transaction:
    """Inject the family coercion / elder exploitation scenario.

    Story: Margaret Chen (74) is manipulated by "Jason" (claiming to be her grandson)
    into making a $4,800 e-Transfer. Jason accompanies her to the branch, logs in
    from his phone, coaches her through support chat, adds himself as payee, and
    initiates the transfer.

    Timeline (relative to fraud at step N):
      N-14: Branch visit — companion noted by staff
      N-12: New device login (Jason's Samsung)
      N-10 to N: Balance check routine STOPS (absence detection)
      N-2:  Support chat with coached language
      N-1:  New payee added (Jason)
      N:    $4,800 TRANSFER to Jason

    Returns the fraud Transaction for the orchestrator to process.
    """
    target = target_persona or MARGARET_CHEN
    account_id = target["account_id"]

    # Step N-14: Branch visit with companion
    event_stream.append(
        Event(
            step=fraud_step - 14,
            timestamp=step_to_datetime(fraud_step - 14),
            event_type=EventType.BRANCH_VISIT,
            account_id=account_id,
            payload={
                "branch": "TD Scarborough Town Centre",
                "note": "Customer accompanied by younger male who identified himself as her grandson. He was answering most questions and guiding the customer through the interaction. Customer seemed confused but agreeable.",
                "staff_member": "Jennifer Walsh",
            },
        )
    )

    # Step N-12: New device login (Jason's phone)
    event_stream.append(
        Event(
            step=fraud_step - 12,
            timestamp=step_to_datetime(fraud_step - 12),
            event_type=EventType.DEVICE_CHANGE,
            account_id=account_id,
            payload={
                "device_id": "dev_jason_samsung",
                "ip_address": "10.0.0.55",
                "location": "Markham, ON",
                "previous_device": target["behavior"]["devices"][0]
                if target.get("behavior", {}).get("devices")
                else "dev_margaret_iphone",
            },
        )
    )
    graph.add_edge(
        account_id,
        "dev_jason_samsung",
        edge_type="USES_DEVICE",
        timestamp=step_to_datetime(fraud_step - 12),
    )

    # Step N-2: Support chat with coached language
    event_stream.append(
        Event(
            step=fraud_step - 2,
            timestamp=step_to_datetime(fraud_step - 2),
            event_type=EventType.SUPPORT_CHAT,
            account_id=account_id,
            payload={
                "channel": "webchat",
                "device_id": "dev_jason_samsung",
                "content": "Hi there. My grandson is helping me set up online banking. I need to add a new payee and I'd like to know what my e-transfer limit is. Can you walk me through how to initiate a wire transfer to a beneficiary account? I want to make sure the funds are transferred promptly.",
                "session_duration_minutes": 12,
                "response_pattern": "slow_then_fast",
            },
        )
    )

    # Step N-1: New payee added (Jason)
    event_stream.append(
        Event(
            step=fraud_step - 1,
            timestamp=step_to_datetime(fraud_step - 1),
            event_type=EventType.PAYEE_ADDED,
            account_id=account_id,
            payload={
                "payee_id": JASON_ACCOUNT_ID,
                "payee_name": "Jason Chen",
                "device_id": "dev_jason_samsung",
                "receiver_id": JASON_ACCOUNT_ID,
            },
        )
    )
    graph.add_edge(
        account_id,
        JASON_ACCOUNT_ID,
        edge_type="PAYS_TO",
        timestamp=step_to_datetime(fraud_step - 1),
    )

    # Jason's account setup (the exploiter)
    graph.add_node(
        JASON_ACCOUNT_ID,
        node_type="account",
        name="Jason Chen",
        age=31,
        location="Markham, ON",
    )
    graph.add_edge(
        JASON_ACCOUNT_ID,
        "dev_jason_samsung",
        edge_type="USES_DEVICE",
        timestamp=step_to_datetime(fraud_step - 12),
    )

    # Robert Williams — another victim Jason exploited (fan-in signal)
    graph.add_node(
        ROBERT_ACCOUNT_ID,
        node_type="account",
        name="Robert Williams",
        age=81,
        location="Etobicoke, ON",
    )
    graph.add_edge(
        ROBERT_ACCOUNT_ID,
        JASON_ACCOUNT_ID,
        edge_type="TRANSACTION",
        timestamp=step_to_datetime(fraud_step - 168),
        amount=3500.0,
    )

    # Step N: The fraud transaction
    fraud_tx = Transaction(
        step=fraud_step,
        timestamp=step_to_datetime(fraud_step),
        type=TransactionType.TRANSFER,
        amount=4800.0,
        sender_id=account_id,
        receiver_id=JASON_ACCOUNT_ID,
        old_balance_sender=5200.0,
        new_balance_sender=400.0,
        old_balance_receiver=150.0,
        new_balance_receiver=4950.0,
        is_fraud=True,
        channel="online",
        description="e-Transfer to Jason Chen",
    )

    # Add the fraud transaction edge to the graph
    graph.add_transaction_edge(
        sender_id=account_id,
        receiver_id=JASON_ACCOUNT_ID,
        transaction=fraud_tx,
    )

    # Log the transaction as an event (orchestrator does this too, but we add it for timeline completeness)
    event_stream.append(
        Event(
            step=fraud_step,
            timestamp=step_to_datetime(fraud_step),
            event_type=EventType.TRANSACTION,
            account_id=account_id,
            payload=fraud_tx.model_dump(),
        )
    )

    return fraud_tx


def inject_account_takeover(
    event_stream: EventStream,
    graph: BrainGraph,
    target_persona: dict | None = None,
    fraud_step: int = 400,
) -> Transaction:
    """Inject the account takeover scenario.

    Story: Attacker gains access via credential compromise, resets password,
    changes email to lock out victim, logs in from new device, and rapidly
    drains the account with multiple transfers to a mule.

    Timeline (relative to fraud at step N):
      N-48: Password reset (attacker gains access)
      N-36: Email change (control recovery channels)
      N-24: Device change (attacker's device)
      N-2:  New payee added (mule)
      N-2:  First transfer $1,200
      N-1:  Second transfer $2,800
      N:    Third transfer $3,500 (main fraud tx returned)

    Returns the largest fraud Transaction for the orchestrator to process.
    """
    target = target_persona or SARAH_MITCHELL
    account_id = target["account_id"]
    prev_device = (
        target["behavior"]["devices"][0]
        if target.get("behavior", {}).get("devices")
        else "dev_sarah_macbook"
    )

    # Step N-48: Password reset
    event_stream.append(
        Event(
            step=fraud_step - 48,
            timestamp=step_to_datetime(fraud_step - 48),
            event_type=EventType.PASSWORD_RESET,
            account_id=account_id,
            payload={
                "method": "email_link",
                "ip_address": "192.168.1.105",
                "device_id": "dev_attacker_laptop",
                "location": "Brampton, ON",
            },
        )
    )

    # Step N-36: Email change
    event_stream.append(
        Event(
            step=fraud_step - 36,
            timestamp=step_to_datetime(fraud_step - 36),
            event_type=EventType.EMAIL_CHANGE,
            account_id=account_id,
            payload={
                "previous_email": "sarah.mitchell@gmail.com",
                "new_email": "sarah.m.2026@tempmail.org",
                "device_id": "dev_attacker_laptop",
            },
        )
    )

    # Step N-24: Device change (attacker's device)
    event_stream.append(
        Event(
            step=fraud_step - 24,
            timestamp=step_to_datetime(fraud_step - 24),
            event_type=EventType.DEVICE_CHANGE,
            account_id=account_id,
            payload={
                "device_id": "dev_attacker_laptop",
                "ip_address": "192.168.1.105",
                "location": "Brampton, ON",
                "previous_device": prev_device,
            },
        )
    )
    graph.add_edge(
        account_id,
        "dev_attacker_laptop",
        edge_type="USES_DEVICE",
        timestamp=step_to_datetime(fraud_step - 24),
    )

    # Mule account setup
    graph.add_node(
        ATO_MULE_ACCOUNT_ID,
        node_type="account",
        name="Unknown",
        location="Brampton, ON",
    )

    # Step N-2: New payee added + first transfer
    event_stream.append(
        Event(
            step=fraud_step - 2,
            timestamp=step_to_datetime(fraud_step - 2),
            event_type=EventType.PAYEE_ADDED,
            account_id=account_id,
            payload={
                "payee_id": ATO_MULE_ACCOUNT_ID,
                "device_id": "dev_attacker_laptop",
                "receiver_id": ATO_MULE_ACCOUNT_ID,
            },
        )
    )
    graph.add_edge(
        account_id,
        ATO_MULE_ACCOUNT_ID,
        edge_type="PAYS_TO",
        timestamp=step_to_datetime(fraud_step - 2),
    )

    tx1 = Transaction(
        step=fraud_step - 2,
        timestamp=step_to_datetime(fraud_step - 2),
        type=TransactionType.TRANSFER,
        amount=1200.0,
        sender_id=account_id,
        receiver_id=ATO_MULE_ACCOUNT_ID,
        old_balance_sender=7500.0,
        new_balance_sender=6300.0,
        old_balance_receiver=0.0,
        new_balance_receiver=1200.0,
        is_fraud=True,
        channel="online",
        description="e-Transfer",
    )
    graph.add_transaction_edge(account_id, ATO_MULE_ACCOUNT_ID, tx1)
    event_stream.append(
        Event(
            step=fraud_step - 2,
            timestamp=step_to_datetime(fraud_step - 2),
            event_type=EventType.TRANSACTION,
            account_id=account_id,
            payload=tx1.model_dump(),
        )
    )

    # Step N-1: Second transfer
    tx2 = Transaction(
        step=fraud_step - 1,
        timestamp=step_to_datetime(fraud_step - 1),
        type=TransactionType.TRANSFER,
        amount=2800.0,
        sender_id=account_id,
        receiver_id=ATO_MULE_ACCOUNT_ID,
        old_balance_sender=6300.0,
        new_balance_sender=3500.0,
        old_balance_receiver=1200.0,
        new_balance_receiver=4000.0,
        is_fraud=True,
        channel="online",
        description="e-Transfer",
    )
    graph.add_transaction_edge(account_id, ATO_MULE_ACCOUNT_ID, tx2)
    event_stream.append(
        Event(
            step=fraud_step - 1,
            timestamp=step_to_datetime(fraud_step - 1),
            event_type=EventType.TRANSACTION,
            account_id=account_id,
            payload=tx2.model_dump(),
        )
    )

    # Step N: Third transfer (main fraud tx — returned)
    fraud_tx = Transaction(
        step=fraud_step,
        timestamp=step_to_datetime(fraud_step),
        type=TransactionType.TRANSFER,
        amount=3500.0,
        sender_id=account_id,
        receiver_id=ATO_MULE_ACCOUNT_ID,
        old_balance_sender=3500.0,
        new_balance_sender=0.0,
        old_balance_receiver=4000.0,
        new_balance_receiver=7500.0,
        is_fraud=True,
        channel="online",
        description="e-Transfer",
    )
    graph.add_transaction_edge(account_id, ATO_MULE_ACCOUNT_ID, fraud_tx)
    event_stream.append(
        Event(
            step=fraud_step,
            timestamp=step_to_datetime(fraud_step),
            event_type=EventType.TRANSACTION,
            account_id=account_id,
            payload=fraud_tx.model_dump(),
        )
    )

    return fraud_tx


def inject_mule_network(
    event_stream: EventStream,
    graph: BrainGraph,
    fraud_step: int = 500,
) -> Transaction:
    """Inject the mule network scenario.

    Story: 5 mule accounts receive funds from various victims. All mules share
    the same device (same IP/device fingerprint). Transfers are synchronized
    within a short window — classic money mule structure.

    Graph signals:
      - Shared identity: 5 accounts all use dev_mule_assembly
      - Hub/fan-in: victims send to mules; mules may funnel to collector
      - Temporal clustering: transfers at N-1, N, N+1

    Timeline:
      N-24: Mules created, all link to shared device
      N-1:  Victim1 -> Mule1 ($800), Victim2 -> Mule2 ($1,200)
      N:    Victim3 -> Mule3 ($2,500) — main fraud tx returned
      N+1:  Victim4 -> Mule4 ($600)

    Returns the largest fraud Transaction for the orchestrator to process.
    """
    victim_ids = ["C_VICTIM_A", "C_VICTIM_B", "C_VICTIM_C", "C_VICTIM_D"]

    # Create 5 mule accounts, all sharing the same device
    for i, mule_id in enumerate(MULE_ACCOUNT_IDS):
        graph.add_node(
            mule_id,
            node_type="account",
            name=f"Mule_{i + 1}",
            location="Mississauga, ON",
        )
        graph.add_edge(
            mule_id,
            MULE_SHARED_DEVICE,
            edge_type="USES_DEVICE",
            timestamp=step_to_datetime(fraud_step - 24),
        )
        event_stream.append(
            Event(
                step=fraud_step - 24,
                timestamp=step_to_datetime(fraud_step - 24),
                event_type=EventType.DEVICE_CHANGE,
                account_id=mule_id,
                payload={
                    "device_id": MULE_SHARED_DEVICE,
                    "ip_address": "10.88.22.17",
                    "location": "Mississauga, ON",
                },
            )
        )

    # Create victim nodes (they send to mules)
    for vid in victim_ids:
        graph.add_node(vid, node_type="account", name="Unknown", location="Various")

    # Synchronized transfers: N-1, N, N+1
    transfers = [
        (fraud_step - 1, victim_ids[0], MULE_ACCOUNT_IDS[0], 800.0),
        (fraud_step - 1, victim_ids[1], MULE_ACCOUNT_IDS[1], 1200.0),
        (fraud_step, victim_ids[2], MULE_ACCOUNT_IDS[2], 2500.0),  # main
        (fraud_step + 1, victim_ids[3], MULE_ACCOUNT_IDS[3], 600.0),
    ]

    fraud_tx = None
    for step, sender, receiver, amount in transfers:
        tx = Transaction(
            step=step,
            timestamp=step_to_datetime(step),
            type=TransactionType.TRANSFER,
            amount=amount,
            sender_id=sender,
            receiver_id=receiver,
            old_balance_sender=amount + 100.0,
            new_balance_sender=100.0,
            old_balance_receiver=0.0,
            new_balance_receiver=amount,
            is_fraud=True,
            channel="online",
            description="e-Transfer",
        )
        graph.add_transaction_edge(sender, receiver, tx)
        event_stream.append(
            Event(
                step=step,
                timestamp=step_to_datetime(step),
                event_type=EventType.TRANSACTION,
                account_id=sender,
                payload=tx.model_dump(),
            )
        )
        if amount == 2500.0:
            fraud_tx = tx

    return fraud_tx


def inject_card_testing(
    event_stream: EventStream,
    graph: BrainGraph,
    merchant_id: str | None = None,
    fraud_step: int = 600,
) -> Transaction:
    """Inject the card testing scenario.

    Story: Attacker tests stolen card numbers with a burst of small payments
    at a merchant. Small amounts ($5–$25) to verify the card works before
    attempting larger fraud. All transactions are first-time at this merchant.

    Graph signals:
      - Edge burst: many transactions to same merchant in short window
      - First-time payee: account has no prior history with this merchant

    Timeline (burst within 2 hours):
      N-1: $5, $9 (first two probes)
      N:   $12, $15, $20 (main burst — return $15 as representative)
      N+1: $8 (final probe)

    Returns a representative fraud Transaction for the orchestrator to process.
    """
    merchant = merchant_id or CARD_TEST_MERCHANT
    account_id = CARD_TESTER_ACCOUNT

    graph.add_node(account_id, node_type="account", name="Unknown", location="Toronto, ON")
    graph.add_node(merchant, node_type="merchant", name="Online Gift Shop", location="Vancouver, BC")

    # Burst of small first-time payments
    amounts = [5.0, 9.0, 12.0, 15.0, 20.0, 8.0]
    steps = [fraud_step - 1, fraud_step - 1, fraud_step, fraud_step, fraud_step, fraud_step + 1]

    fraud_tx = None
    balance = 500.0
    for i, (step, amount) in enumerate(zip(steps, amounts)):
        tx = Transaction(
            step=step,
            timestamp=step_to_datetime(step),
            type=TransactionType.PAYMENT,
            amount=amount,
            sender_id=account_id,
            receiver_id=merchant,
            old_balance_sender=balance,
            new_balance_sender=balance - amount,
            old_balance_receiver=0.0,
            new_balance_receiver=amount,
            is_fraud=True,
            channel="online",
            description=merchant,
        )
        balance -= amount
        graph.add_transaction_edge(account_id, merchant, tx)
        event_stream.append(
            Event(
                step=step,
                timestamp=step_to_datetime(step),
                event_type=EventType.TRANSACTION,
                account_id=account_id,
                payload={**tx.model_dump(), "merchant_category": "gift_card"},
            )
        )
        if amount == 15.0:
            fraud_tx = tx

    return fraud_tx
