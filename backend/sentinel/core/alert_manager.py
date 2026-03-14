"""Alert manager — groups related reports and prevents analyst fatigue."""

from __future__ import annotations

from datetime import datetime

from sentinel.models.report import AlertBundle, CaseReport


class AlertManager:
    """Collect case reports and bundle related alerts."""

    def __init__(self) -> None:
        self._bundles: list[AlertBundle] = []
        self._reports: list[CaseReport] = []

    def create_alert(self, report: CaseReport) -> None:
        self._reports.append(report)

        for bundle in self._bundles:
            if bundle.status != "open":
                continue
            overlapping = set(bundle.related_account_ids) & {
                report.transaction.sender_id,
                report.transaction.receiver_id,
            }
            if overlapping:
                bundle.case_reports.append(report)
                bundle.related_account_ids = list(
                    set(bundle.related_account_ids)
                    | {report.transaction.sender_id, report.transaction.receiver_id}
                )
                return

        bundle = AlertBundle(
            related_account_ids=[
                report.transaction.sender_id,
                report.transaction.receiver_id,
            ],
            case_reports=[report],
        )
        self._bundles.append(bundle)

    def get_bundles(self, status: str = "open") -> list[AlertBundle]:
        return [b for b in self._bundles if b.status == status]

    def get_all_bundles(self) -> list[AlertBundle]:
        return list(self._bundles)
