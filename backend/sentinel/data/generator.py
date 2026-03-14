"""World state builder — loads data and populates warm state on startup."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
        """Inject a fraud scenario into the live world state."""
        raise NotImplementedError(
            f"Scenario '{scenario_name}' not implemented yet — coming in Phase 2."
        )
