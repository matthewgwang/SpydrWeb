"""Layer 0 — Append-only in-memory event log.

Every module writes events here; every detection layer reads from here.
Thread-safe for concurrent access from WebSocket feed and detection pipeline.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from typing import Optional

from app.models.events import Event, EventType


class EventStream:
    """Append-only event log. Singleton instance shared via app.state."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._lock = threading.Lock()

    def append(self, event: Event) -> None:
        """Append a new event. Thread-safe."""
        with self._lock:
            self._events.append(event)

    def query(
        self,
        account_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list[Event]:
        """Filter events. All parameters optional; combine as needed.

        Returns events matching all provided filters, sorted by timestamp ascending.
        ``since`` is inclusive lower bound, ``until`` is inclusive upper bound.
        """
        with self._lock:
            result = self._events

        if account_id is not None:
            result = [e for e in result if e.account_id == account_id]
        if event_type is not None:
            result = [e for e in result if e.event_type == event_type]
        if since is not None:
            result = [e for e in result if e.timestamp >= since]
        if until is not None:
            result = [e for e in result if e.timestamp <= until]

        result.sort(key=lambda e: e.timestamp)

        if limit is not None:
            result = result[-limit:]  # most recent N

        return result

    def get_all(self) -> list[Event]:
        """Return all events, sorted by timestamp."""
        with self._lock:
            events = list(self._events)
        events.sort(key=lambda e: e.timestamp)
        return events

    def get_window(
        self,
        account_id: str,
        window_minutes: int = 60,
        before: Optional[datetime] = None,
    ) -> list[Event]:
        """Return events for account_id in the last N minutes.

        If before is None, uses datetime.now(UTC) as reference.
        """
        ref = before or datetime.now(UTC)
        since = ref - timedelta(minutes=window_minutes)
        return self.query(account_id=account_id, since=since, until=ref)
