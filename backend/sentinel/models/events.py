from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Lowercase values to match implementation_details and wiring_guide."""
    TRANSACTION = "transaction"
    LOGIN = "login"
    PASSWORD_RESET = "password_reset"
    EMAIL_CHANGE = "email_change"
    PAYEE_ADDED = "payee_added"
    DEVICE_CHANGE = "device_change"
    SUPPORT_CHAT = "support_chat"
    BALANCE_CHECK = "balance_check"
    BRANCH_VISIT = "branch_visit"
    PHONE_CALL = "phone_call"
    LIMIT_INQUIRY = "limit_inquiry"
    SETTINGS_CHANGE = "settings_change"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step: int = 0
    event_type: EventType
    account_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
