from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """PaySim transaction types."""
    CASH_IN = "CASH_IN"
    CASH_OUT = "CASH_OUT"
    DEBIT = "DEBIT"
    PAYMENT = "PAYMENT"
    TRANSFER = "TRANSFER"


class Transaction(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sender_id: str
    receiver_id: str
    amount: float
    channel: Optional[str] = None
    merchant_category: Optional[str] = None
    description: Optional[str] = None

    # PaySim fields for contextual impossibility checks
    step: Optional[int] = None
    type: Optional[TransactionType] = None
    old_balance_sender: Optional[float] = None
    new_balance_sender: Optional[float] = None
    old_balance_receiver: Optional[float] = None
    new_balance_receiver: Optional[float] = None
    is_fraud: Optional[bool] = None


class TransactionContext(BaseModel):
    """Enriched context assembled around a transaction for detection layers."""
    transaction: Transaction
    sender_id: str
    receiver_id: str
    recent_sender_events: list = Field(default_factory=list)
    recent_receiver_events: list = Field(default_factory=list)
