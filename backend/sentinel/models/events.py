from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    TRANSACTION = "TRANSACTION"
    LOGIN = "LOGIN"
    PASSWORD_RESET = "PASSWORD_RESET"
    EMAIL_CHANGE = "EMAIL_CHANGE"
    PAYEE_ADDED = "PAYEE_ADDED"
    DEVICE_CHANGE = "DEVICE_CHANGE"
    SUPPORT_CHAT = "SUPPORT_CHAT"
    BALANCE_CHECK = "BALANCE_CHECK"
    BRANCH_VISIT = "BRANCH_VISIT"
    PHONE_CALL = "PHONE_CALL"
    LIMIT_INQUIRY = "LIMIT_INQUIRY"
    SETTINGS_CHANGE = "SETTINGS_CHANGE"


class Event(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step: int = 0
    event_type: EventType
    account_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
