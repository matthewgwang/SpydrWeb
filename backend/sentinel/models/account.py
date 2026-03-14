from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaselineStats(BaseModel):
    """Rolling behavioural statistics for an account.

    All statistics use exponential decay (weight = e^(-lambda * age_in_days))
    so recent activity contributes more than old history.
    """
    avg_amount: float = 0.0
    std_amount: float = 0.0
    avg_daily_frequency: float = 0.0
    avg_weekly_frequency: float = 0.0
    typical_hours: list[int] = Field(default_factory=list)
    typical_merchants: dict[str, int] = Field(default_factory=dict)
    typical_channels: dict[str, int] = Field(default_factory=dict)
    typical_transaction_types: dict[str, int] = Field(default_factory=dict)
    login_frequency_daily: float = 0.0
    balance_check_frequency_daily: float = 0.0
    last_activity: Optional[datetime] = None
    decay_factor: float = 0.05
    days_of_history: int = 0


class CommunicationFingerprint(BaseModel):
    """Baseline communication style derived from historical support interactions."""
    typical_vocabulary_level: str = "simple"
    typical_tone: str = "polite"
    typical_topics: list[str] = Field(default_factory=list)
    avg_interaction_frequency_monthly: float = 0.0
    avg_message_length_words: int = 0
    uses_technical_banking_terms: bool = False
    typical_channels: list[str] = Field(default_factory=list)
    baseline_sentiment: str = "neutral"
    sample_phrases: list[str] = Field(default_factory=list)


class VulnerabilityFactor(BaseModel):
    factor: str
    description: str
    weight: float = 0.0


class VulnerabilityScore(BaseModel):
    """Behavioral vulnerability assessment (NOT demographic profiling)."""
    score: float = 0.0
    factors: list[VulnerabilityFactor] = Field(default_factory=list)
    transaction_diversity_trend: float = 0.0
    social_spending_trend: float = 0.0
    digital_literacy_level: str = "low"
    routine_rigidity: float = 0.0
    recent_life_disruption: bool = False


class RecipientRiskScore(BaseModel):
    """Receiver-side risk metrics for collection / mule detection."""
    first_time_sender_count_7d: int = 0
    avg_relationship_duration_days: float = 0.0
    receive_to_send_ratio: float = 0.0
    inbound_velocity_24h: float = 0.0
    is_receive_only: bool = False
    connected_to_other_vulnerable_customers: bool = False
    total_inbound_amount_7d: float = 0.0


class AccountProfile(BaseModel):
    account_id: str
    name: str = ""
    age: Optional[int] = None
    location: Optional[str] = None
    account_created: str = ""
    account_type: str = "retail"
    summary_text: str = ""
    communication_fingerprint: Optional[CommunicationFingerprint] = None
    baseline: Optional[BaselineStats] = None
    vulnerability: Optional[VulnerabilityScore] = None
    recipient_risk: Optional[RecipientRiskScore] = None
    devices: list[str] = Field(default_factory=list)
    known_payees: list[str] = Field(default_factory=list)
    profile_confidence: float = 1.0
