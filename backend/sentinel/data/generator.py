"""World state builder — loads data and populates warm state on startup.

Generates 90 days of normal transaction/event history for each persona,
computes baselines, populates the graph, and builds profiles so the
pipeline is ready to process incoming transactions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel.accounts.baselines import BaselineComputer
    from sentinel.accounts.profile_builder import ProfileBuilder
    from sentinel.accounts.store import AccountStore
    from sentinel.accounts.vulnerability import VulnerabilityScorer
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream

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
        from sentinel.data.augment_comms import generate_normal_comms
        from sentinel.data.profiles import ALL_PERSONAS
        from sentinel.data.transactions import generate_normal_history

        for persona in ALL_PERSONAS:
            account_id = persona["account_id"]
            logger.info("Building world state for %s (%s)", persona.get("name"), account_id)

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
                profile = await self.profile_builder.build_profile(
                    account_id, self.event_stream, self.brain_graph
                )
                existing = self.account_store.get_profile(account_id)
                if existing:
                    existing.summary_text = profile.summary_text
                    existing.communication_fingerprint = profile.communication_fingerprint
            except Exception:
                logger.warning("LLM profile build failed for %s, using baseline only", account_id)

            last_tx_time = transactions[-1].timestamp if transactions else None
            vulnerability = self.vulnerability_scorer.compute(
                account_id, profile, self.event_stream, last_tx_time
            )
            stored = self.account_store.get_profile(account_id)
            if stored:
                stored.vulnerability = vulnerability

        logger.info("World state built for %d personas", len(ALL_PERSONAS))

    async def inject_scenario(self, scenario_name: str) -> None:
        """Inject a fraud scenario into the live world state.

        Scenario injection is Track B (scenarios.py). This method
        is the integration point that Track B will fill in.
        """
        raise NotImplementedError(
            f"Scenario '{scenario_name}' — inject via Track B scenarios module."
        )
