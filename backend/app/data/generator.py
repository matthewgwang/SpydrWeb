"""World state builder — loads data and populates warm state on startup.

Generates 90 days of normal transaction/event history for each persona,
computes baselines, populates the graph, and builds profiles so the
pipeline is ready to process incoming transactions.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.data.scenarios import (
    inject_account_takeover,
    inject_card_testing,
    inject_elder_exploitation,
    inject_mule_network,
)

if TYPE_CHECKING:
    from app.accounts.baselines import BaselineComputer
    from app.accounts.profile_builder import ProfileBuilder
    from app.accounts.store import AccountStore
    from app.accounts.vulnerability import VulnerabilityScorer
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream

logger = logging.getLogger(__name__)


class WorldStateBuilder:
    """Build the warm world state from persona definitions at startup."""

    def __init__(
        self,
        event_stream: EventStream,
        account_store: AccountStore,
        brain_graph: BrainGraph,
        baseline_computer: BaselineComputer,
        profile_builder: ProfileBuilder,
        vulnerability_scorer: VulnerabilityScorer,
    ) -> None:
        self.event_stream = event_stream
        self.account_store = account_store
        self.brain_graph = brain_graph
        self.baseline_computer = baseline_computer
        self.profile_builder = profile_builder
        self.vulnerability_scorer = vulnerability_scorer

    async def build(self, days: int = 90) -> None:
        """Build warm world state from all personas.

        For each persona:
        1. Create account profile from persona definition
        2. Generate normal transaction + event history
        3. Generate normal communication events
        4. Append events to the event stream
        5. Add transaction edges to the graph
        6. Compute behavioral baselines
        7. Build LLM-generated profile summaries
        8. Compute vulnerability scores
        """
        from app.data.augment_comms import generate_normal_comms
        from app.data.profiles import ALL_PERSONAS
        from app.data.transactions import generate_normal_history

        total = len(ALL_PERSONAS)
        for idx, persona in enumerate(ALL_PERSONAS, 1):
            account_id = persona["account_id"]
            name = persona.get("name", account_id)
            print(f"[WORLD] {idx}/{total} Building: {name} ({account_id})")

            profile = self.account_store.create_from_persona(persona)

            transactions, events = generate_normal_history(persona, days=days)
            comms = generate_normal_comms(persona, days=days)

            for event in events:
                self.event_stream.append(event)
            for event in comms:
                self.event_stream.append(event)

            for tx in transactions:
                self.brain_graph.add_transaction_edge(
                    sender_id=tx.sender_id,
                    receiver_id=tx.receiver_id,
                    transaction=tx,
                )

            all_events = self.event_stream.query(account_id=account_id)
            baseline = self.baseline_computer.compute(
                account_id=account_id,
                events=all_events,
                transactions=transactions,
            )
            profile.baseline = baseline

            try:
                import asyncio
                llm_profile = await asyncio.wait_for(
                    self.profile_builder.build_profile(
                        account_id, self.event_stream, self.brain_graph
                    ),
                    timeout=15.0,
                )
                existing = self.account_store.get_profile(account_id)
                if existing:
                    existing.summary_text = llm_profile.summary_text
                    existing.communication_fingerprint = llm_profile.communication_fingerprint
                print(f"[WORLD]   LLM profile OK for {name}")
            except asyncio.TimeoutError:
                print(f"[WORLD]   LLM profile timeout for {name}, using baseline")
            except Exception as exc:
                print(f"[WORLD]   LLM profile failed for {name}: {exc}")

            last_tx_time = (
                transactions[-1].timestamp if transactions else datetime.now(UTC)
            )
            vulnerability = self.vulnerability_scorer.compute(
                account_id, profile, self.event_stream, last_tx_time
            )
            stored = self.account_store.get_profile(account_id)
            if stored:
                stored.vulnerability = vulnerability

        print(f"[WORLD] Done — {total} personas built")

    async def inject_scenario(self, scenario_name: str):
        """Inject a fraud scenario into the live world state.

        Returns the fraud transaction(s) for the orchestrator to process.
        """
        if scenario_name == "elder_exploitation":
            return inject_elder_exploitation(
                self.event_stream,
                self.brain_graph,
                target_persona=None,
                fraud_step=342,
            )
        if scenario_name == "account_takeover":
            return inject_account_takeover(
                self.event_stream,
                self.brain_graph,
                target_persona=None,
                fraud_step=400,
            )
        if scenario_name == "mule_network":
            return inject_mule_network(
                self.event_stream,
                self.brain_graph,
                fraud_step=500,
            )
        if scenario_name == "card_testing":
            return inject_card_testing(
                self.event_stream,
                self.brain_graph,
                merchant_id=None,
                fraud_step=600,
            )
        raise NotImplementedError(
            f"Scenario '{scenario_name}' — inject via Track B scenarios module."
        )
