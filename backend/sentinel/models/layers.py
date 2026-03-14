from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FraudType(str, Enum):
    ELDER_EXPLOITATION = "ELDER_EXPLOITATION"
    ACCOUNT_TAKEOVER = "ACCOUNT_TAKEOVER"
    MULE_NETWORK = "MULE_NETWORK"
    CARD_TESTING = "CARD_TESTING"
    UNKNOWN = "UNKNOWN"


class LayerSignal(BaseModel):
    """Standard output shape for every detection layer (1-5)."""
    layer_id: int
    layer_name: str
    triggered: bool = False
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    explanation: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)


class LayerResult(BaseModel):
    """Wrapper that collects signals from all layers for one transaction."""
    signals: list[LayerSignal] = Field(default_factory=list)

    @property
    def triggered_signals(self) -> list[LayerSignal]:
        return [s for s in self.signals if s.triggered]

    @property
    def max_confidence(self) -> float:
        triggered = self.triggered_signals
        return max((s.confidence for s in triggered), default=0.0)


class TestPlan(BaseModel):
    """Output of Step 2 — AI-predicted fraud types and layer strategy."""
    predicted_fraud_types: list[FraudType] = Field(default_factory=list)
    layer_priority: list[int] = Field(default_factory=list)
    layer_weights: dict[int, float] = Field(default_factory=dict)
