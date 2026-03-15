"""Stub layers — placeholders until Track A implements layers 2, 4, 5."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.layers import LayerSignal
from app.models.report import EvidenceBrief

from app.layers.base import DetectionLayer

if TYPE_CHECKING:
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream
    from app.models.account import AccountProfile
    from app.models.transaction import Transaction


class StubLayer(DetectionLayer):
    """Placeholder for layers 2, 3, 4 — returns no signal."""

    def __init__(self, layer_id: int, layer_name: str) -> None:
        self.layer_id = layer_id
        self.layer_name = layer_name

    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> LayerSignal:
        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=False,
            confidence=0.0,
            explanation="",
            evidence={},
            severity="low",
        )


class SynthesisStubLayer(DetectionLayer):
    """Placeholder for Layer 5 — returns minimal EvidenceBrief."""

    layer_id = 5
    layer_name = "synthesis"

    async def analyze(self, *args, **kwargs) -> LayerSignal:
        return LayerSignal(
            layer_id=5,
            layer_name="synthesis",
            triggered=False,
            confidence=0.0,
            explanation="",
            evidence={},
            severity="low",
        )

    async def synthesize(self, **kwargs) -> EvidenceBrief:
        return EvidenceBrief(
            narrative="Synthesis not yet implemented (Track A).",
            signals=kwargs.get("all_signals", []),
            confidence_score=0.0,
        )
