from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaselineStats(BaseModel):
    """Rolling behavioural statistics for an account.

    All statistics use exponential decay (weight = e^(-λ * age_in_days))
    so recent activity contributes more than old history.
    """
    avg_amount: float = 0.0
    std_amount: float = 0.0
    avg_frequency: float = 0.0          # transactions per day
    typical_hours: list[int] = Field(default_factory=list)
    typical_merchants: dict[str, int] = Field(default_factory=dict)
    typical_channels: dict[str, int] = Field(default_factory=dict)
    login_pattern: dict[str, float] = Field(default_factory=dict)
    last_activity: Optional[datetime] = None
    decay_factor: float = 0.05          # λ for time-weighted decay


class RecipientRiskScore(BaseModel):
    """Receiver-side risk metrics for collection / mule detection."""
    first_time_sender_count_7d: int = 0
    avg_relationship_duration_days: float = 0.0
    receive_to_send_ratio: float = 0.0
    inbound_velocity_24h: float = 0.0
    is_receive_only: bool = False


class ProfileSummary(BaseModel):
    """LLM-generated natural-language summary of an account's behaviour."""
    text: str = ""
    generated_at: Optional[datetime] = None


class AccountProfile(BaseModel):
    account_id: str
    name: str = ""
    age: Optional[int] = None
    location: Optional[str] = None
    summary: ProfileSummary = Field(default_factory=ProfileSummary)
    baseline: BaselineStats = Field(default_factory=BaselineStats)
    recipient_risk: RecipientRiskScore = Field(default_factory=RecipientRiskScore)
    events: list = Field(default_factory=list)
    devices: list[str] = Field(default_factory=list)
    payees: list[str] = Field(default_factory=list)
    profile_confidence: float = 1.0     # decays when profile is stale
    created_at: datetime = Field(default_factory=datetime.utcnow)
