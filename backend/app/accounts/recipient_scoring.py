"""Recipient risk scorer — receiver-side risk assessment.

Computes all RecipientRiskScore fields from the event stream and graph
to detect collection / mule patterns.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from app.models.account import RecipientRiskScore

if TYPE_CHECKING:
    from app.brain.graph import BrainGraph
    from app.core.event_stream import EventStream


class RecipientScorer:
    def compute_risk(
        self,
        receiver_id: str,
        event_stream: EventStream,
        graph: BrainGraph,
        vulnerability_scores: dict[str, float] | None = None,
        reference_time: datetime | None = None,
    ) -> RecipientRiskScore:
        now = reference_time or datetime.now(UTC)
        vuln_scores = vulnerability_scores or {}

        in_edges = list(graph.graph.in_edges(receiver_id, data=True)) if receiver_id in graph.graph else []
        out_edges = list(graph.graph.out_edges(receiver_id, data=True)) if receiver_id in graph.graph else []

        tx_in_edges = [e for e in in_edges if e[2].get("edge_type") == "TRANSACTION"]
        tx_out_edges = [e for e in out_edges if e[2].get("edge_type") == "TRANSACTION"]

        # first_time_sender_count_7d
        week_ago = now - timedelta(days=7)
        recent_senders: set[str] = set()
        all_senders_before: set[str] = set()
        for src, _, data in tx_in_edges:
            ts = data.get("timestamp")
            if ts and ts >= week_ago:
                recent_senders.add(src)
            elif ts and ts < week_ago:
                all_senders_before.add(src)
        first_time_senders_7d = len(recent_senders - all_senders_before)

        # avg_relationship_duration_days
        sender_first_seen: dict[str, datetime] = {}
        for src, _, data in tx_in_edges:
            ts = data.get("timestamp")
            if ts:
                if src not in sender_first_seen or ts < sender_first_seen[src]:
                    sender_first_seen[src] = ts
        if sender_first_seen:
            durations = [(now - first).days for first in sender_first_seen.values()]
            avg_relationship = sum(durations) / len(durations)
        else:
            avg_relationship = 0.0

        # receive_to_send_ratio
        total_inbound = len(tx_in_edges)
        total_outbound = len(tx_out_edges)
        receive_to_send = total_inbound / max(total_outbound, 1)

        # inbound_velocity_24h
        day_ago = now - timedelta(hours=24)
        recent_24h = [e for e in tx_in_edges if e[2].get("timestamp") and e[2]["timestamp"] >= day_ago]
        inbound_velocity = len(recent_24h) / 24.0

        # is_receive_only
        is_receive_only = total_inbound > 0 and total_outbound == 0

        # connected_to_other_vulnerable_customers
        senders = {e[0] for e in tx_in_edges}
        vulnerable_senders = [s for s in senders if vuln_scores.get(s, 0.0) > 0.6]
        connected_vulnerable = len(vulnerable_senders) >= 2

        # total_inbound_amount_7d
        total_amount_7d = sum(
            e[2].get("amount", 0.0)
            for e in tx_in_edges
            if e[2].get("timestamp") and e[2]["timestamp"] >= week_ago
        )

        return RecipientRiskScore(
            first_time_sender_count_7d=first_time_senders_7d,
            avg_relationship_duration_days=avg_relationship,
            receive_to_send_ratio=receive_to_send,
            inbound_velocity_24h=inbound_velocity,
            is_receive_only=is_receive_only,
            connected_to_other_vulnerable_customers=connected_vulnerable,
            total_inbound_amount_7d=total_amount_7d,
        )
