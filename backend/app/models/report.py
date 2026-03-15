from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from app.models.account import AccountProfile
from app.models.layers import ExploitationTactic, FraudType, LayerSignal
from app.models.transaction import Transaction


class Action(str, Enum):
    ALLOW = "allow"
    DELAY = "delay"
    HOLD = "hold"
    REFER = "refer"


class InterventionRecommendation(BaseModel):
    action: str
    reason: str
    urgency: str = "LOW"
    sensitivity_notes: str = ""


class TimelineEntry(BaseModel):
    timestamp: datetime
    step: int = 0
    event_type: str = ""
    description: str
    layer_source: str = ""
    significance: str = ""


class EvidenceBrief(BaseModel):
    """Narrative report produced by Layer 5 synthesis."""
    narrative: str = ""
    timeline: list[TimelineEntry] = Field(default_factory=list)
    signals: list[LayerSignal] = Field(default_factory=list)
    exploitation_tactic: ExploitationTactic = ExploitationTactic.UNKNOWN
    manipulation_indicators: list[str] = Field(default_factory=list)
    interventions: list[InterventionRecommendation] = Field(default_factory=list)
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    what_traditional_systems_missed: str = ""


class CaseReport(BaseModel):
    """Per implementation_details: transaction, sender_profile, receiver_profile required; brain_overlay is dict."""
    id: str = Field(default_factory=lambda: uuid4().hex)
    transaction_id: str
    transaction: Transaction
    sender_profile: AccountProfile
    receiver_profile: AccountProfile
    evidence_brief: Optional[EvidenceBrief] = None
    brain_overlay: Optional[dict[str, Any]] = None
    recommended_action: Action = Action.ALLOW
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    fast_pathed: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    analyst_feedback: Optional[dict] = None


class AlertBundle(BaseModel):
    """Groups related CaseReports to prevent analyst fatigue."""
    bundle_id: str = Field(default_factory=lambda: uuid4().hex)
    related_account_ids: list[str] = Field(default_factory=list)
    case_reports: list[CaseReport] = Field(default_factory=list)
    primary_fraud_type: FraudType = FraudType.UNKNOWN
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: str = "open"
