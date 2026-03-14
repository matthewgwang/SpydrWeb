"""Recipient risk scorer — receiver-side risk assessment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sentinel.models.account import RecipientRiskScore

if TYPE_CHECKING:
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.event_stream import EventStream


class RecipientScorer:
    """Compute receiver-side risk metrics.

    Full implementation comes in Phase 1.
    """

    def compute_risk(
        self,
        receiver_id: str,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> RecipientRiskScore:
        return RecipientRiskScore()
