"""World state builder — loads data and populates warm state on startup."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.data.scenarios import (
    inject_account_takeover,
    inject_card_testing,
    inject_elder_exploitation,
    inject_mule_network,
)

if TYPE_CHECKING:
    from sentinel.accounts.baselines import BaselineComputer
    from sentinel.accounts.profile_builder import ProfileBuilder
    from sentinel.accounts.store import AccountStore
    from sentinel.accounts.vulnerability import VulnerabilityScorer
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream


class WorldStateBuilder:
    """Build the warm world state from persona definitions at startup.

    Full implementation comes in Phase 2 (data generation).
    """

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

    async def build(self) -> None:
        """Build warm world state. Placeholder — Phase 2 fills this in."""
        pass

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
            f"Scenario '{scenario_name}' not implemented yet — coming in Phase 2."
        )
