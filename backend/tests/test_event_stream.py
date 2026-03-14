"""Tests for Layer 0 — EventStream."""

from datetime import datetime, timedelta

import pytest

from sentinel.core.event_stream import EventStream
from sentinel.models.events import Event, EventType


def test_append_and_get_all():
    stream = EventStream()
    e = Event(step=1, timestamp=datetime.utcnow(), event_type=EventType.LOGIN, account_id="A001")
    stream.append(e)
    assert len(stream.get_all()) == 1
    assert stream.get_all()[0].account_id == "A001"


def test_query_by_account():
    stream = EventStream()
    stream.append(Event(step=1, timestamp=datetime(2026, 2, 1, 9, 0), event_type=EventType.TRANSACTION, account_id="A001"))
    stream.append(Event(step=2, timestamp=datetime(2026, 2, 1, 10, 0), event_type=EventType.TRANSACTION, account_id="A002"))
    result = stream.query(account_id="A001")
    assert len(result) == 1
    assert result[0].account_id == "A001"


def test_query_by_event_type():
    stream = EventStream()
    stream.append(Event(step=1, timestamp=datetime(2026, 2, 1, 9, 0), event_type=EventType.BALANCE_CHECK, account_id="A001"))
    stream.append(Event(step=2, timestamp=datetime(2026, 2, 1, 10, 0), event_type=EventType.TRANSACTION, account_id="A001"))
    result = stream.query(account_id="A001", event_type=EventType.TRANSACTION)
    assert len(result) == 1
    assert result[0].event_type == EventType.TRANSACTION


def test_query_since():
    stream = EventStream()
    stream.append(Event(step=1, timestamp=datetime(2026, 2, 1, 8, 0), event_type=EventType.TRANSACTION, account_id="A001"))
    stream.append(Event(step=2, timestamp=datetime(2026, 2, 1, 10, 0), event_type=EventType.TRANSACTION, account_id="A001"))
    since = datetime(2026, 2, 1, 9, 0)
    result = stream.query(account_id="A001", since=since)
    assert len(result) == 1
    assert result[0].step == 2


def test_get_window():
    stream = EventStream()
    stream.append(Event(step=1, timestamp=datetime(2026, 2, 1, 9, 0), event_type=EventType.BALANCE_CHECK, account_id="A001"))
    stream.append(Event(step=2, timestamp=datetime(2026, 2, 1, 10, 0), event_type=EventType.TRANSACTION, account_id="A001"))
    before = datetime(2026, 2, 1, 10, 30)
    result = stream.get_window("A001", window_minutes=120, before=before)
    assert len(result) == 2
