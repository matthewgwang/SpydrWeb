"""Abstract base class for all detection layers (1-5)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.models.layers import LayerSignal

if TYPE_CHECKING:
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream
    from app.models.account import AccountProfile
    from app.models.transaction import Transaction


class DetectionLayer(ABC):
    """Every detection layer implements this interface.

    The orchestrator calls analyze() on each layer uniformly.
    Track A implements layers 2 and 4; Track B implements layers 1 and 3.
    Layer 5 (synthesis) has a separate synthesize() method.
    """

    layer_id: int
    layer_name: str

    @abstractmethod
    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> LayerSignal | list[LayerSignal]:
        """Analyze a transaction and return signal(s).

        Returns a single LayerSignal or a list (rules engine returns multiple).
        """
        ...
