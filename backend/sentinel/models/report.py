from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from sentinel.models.graph_models import BrainOverlay
from sentinel.models.layers import FraudType, LayerSignal


class Action(str, Enum):
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    BLOCK = "BLOCK"
    REFER = "REFER"


class TimelineEntry(BaseModel):
    timestamp: datetime
    description: str
    source_layer: Optional[int] = None


class EvidenceBrief(BaseModel):
    """Narrative report produced by Layer 5 synthesis."""
    narrative: str = ""
    timeline: list[TimelineEntry] = Field(default_factory=list)
    signals: list[LayerSignal] = Field(default_factory=list)
    fraud_pattern: str = ""
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)


class CaseReport(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    transaction_id: str
    evidence_brief: EvidenceBrief = Field(default_factory=EvidenceBrief)
    brain_overlay: BrainOverlay = Field(default_factory=BrainOverlay)
    recommended_action: Action = Action.ALLOW
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fast_pathed: bool = False


class AlertBundle(BaseModel):
    """Groups related CaseReports to prevent analyst fatigue."""
    bundle_id: str = Field(default_factory=lambda: uuid4().hex)
    related_account_ids: list[str] = Field(default_factory=list)
    case_reports: list[CaseReport] = Field(default_factory=list)
    primary_fraud_type: FraudType = FraudType.UNKNOWN
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "open"
