"""Feedback store — records analyst decisions for future learning."""

from __future__ import annotations

from datetime import datetime


class FeedbackStore:
    def __init__(self) -> None:
        self._records: list[dict] = []

    def record(
        self, report_id: str, action: str, fraud_type: str = "", notes: str = ""
    ) -> None:
        self._records.append(
            {
                "report_id": report_id,
                "action": action,
                "fraud_type": fraud_type,
                "notes": notes,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_all(self) -> list[dict]:
        return list(self._records)
