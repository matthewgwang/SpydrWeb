from __future__ import annotations

from datetime import datetime
from enum import Enum
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
    step: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: TransactionType = TransactionType.PAYMENT
    amount: float
    sender_id: str
    receiver_id: str
    old_balance_sender: float = 0.0
    new_balance_sender: float = 0.0
    old_balance_receiver: float = 0.0
    new_balance_receiver: float = 0.0
    is_fraud: bool = False
    channel: str = "online"
    description: str = ""


class TransactionContext(BaseModel):
    """Enriched context assembled around a transaction for detection layers."""
    transaction: Transaction
    sender_id: str
    receiver_id: str
    recent_sender_events: list = Field(default_factory=list)
    recent_receiver_events: list = Field(default_factory=list)
