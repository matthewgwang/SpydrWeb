"""Brain overlay — structural context for the orchestrator (Step 7).

Combines GraphAnalyzer, GraphVelocityMonitor, and RelationshipAnalyzer
to produce a single structural assessment for each transaction.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from app.models.events import EventType

if TYPE_CHECKING:
    from app.brain.analysis import GraphAnalyzer
    from app.brain.graph import BrainGraph
    from app.brain.velocity import GraphVelocityMonitor
    from app.core.event_stream import EventStream
    from app.models.transaction import Transaction


class RelationshipAnalyzer:
    """Reconstructs interaction history between two entities."""

    def __init__(self, graph: BrainGraph) -> None:
        self.graph = graph

    def reconstruct_timeline(
        self,
        entity_a: str,
        entity_b: str,
        event_stream: EventStream,
    ) -> list[dict[str, Any]]:
        """Chronological list of all interactions between two entities.

        Merges graph edges (transactions) with event stream (payee additions,
        device changes, etc.) into a single timeline.
        """
        entries: list[dict[str, Any]] = []

        # 1. Graph edges between entity_a and entity_b (both directions)
        for (u, v), get_data in [
            ((entity_a, entity_b), lambda: self.graph.graph.get_edge_data(entity_a, entity_b)),
            ((entity_b, entity_a), lambda: self.graph.graph.get_edge_data(entity_b, entity_a)),
        ]:
            edge_data = get_data()
            if not edge_data:
                continue
            for _key, data in edge_data.items():
                ts = data.get("timestamp")
                if ts and isinstance(ts, datetime):
                    entries.append({
                        "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
                        "type": data.get("edge_type", "TRANSACTION"),
                        "from": u,
                        "to": v,
                        "amount": data.get("amount"),
                        "tx_id": data.get("tx_id"),
                        "details": data,
                    })

        # 2. Event stream: events involving either account that reference the other
        for account_id in (entity_a, entity_b):
            other_id = entity_b if account_id == entity_a else entity_a
            events = event_stream.query(account_id=account_id)
            for ev in events:
                payload = ev.payload or {}
                refs_other = (
                    payload.get("receiver_id") == other_id
                    or payload.get("sender_id") == other_id
                    or payload.get("payee_id") == other_id
                    or payload.get("account_id") == other_id
                )
                if ev.event_type == EventType.TRANSACTION and refs_other:
                    # May duplicate graph edge; we'll dedupe by timestamp+type
                    entries.append({
                        "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp),
                        "type": ev.event_type.value,
                        "from": payload.get("sender_id", account_id),
                        "to": payload.get("receiver_id", other_id),
                        "amount": payload.get("amount"),
                        "details": payload,
                    })
                elif ev.event_type in (
                    EventType.PAYEE_ADDED,
                    EventType.DEVICE_CHANGE,
                    EventType.SUPPORT_CHAT,
                ) and (refs_other or other_id in str(payload)):
                    entries.append({
                        "timestamp": ev.timestamp.isoformat() if hasattr(ev.timestamp, "isoformat") else str(ev.timestamp),
                        "type": ev.event_type.value,
                        "from": account_id,
                        "to": other_id,
                        "details": payload,
                    })

        # 3. Sort by timestamp
        entries.sort(key=lambda e: e["timestamp"])

        # 4. Dedupe (graph + event stream can overlap)
        seen: set[tuple[str, str, str, str, str]] = set()
        unique: list[dict[str, Any]] = []
        for e in entries:
            key = (
                e["timestamp"],
                e["type"],
                e.get("from", ""),
                e.get("to", ""),
                str(e.get("amount", "")),
            )
            if key not in seen:
                seen.add(key)
                unique.append(e)

        return unique


class BrainOverlayEngine:
    """Step 7 — structural context overlay.

    Combines graph analysis, velocity monitoring, and relationship reconstruction.
    Returns a dict for the orchestrator (elevated, velocity_deviation, structural_signals).
    """

    def __init__(
        self,
        graph: BrainGraph,
        analyzer: GraphAnalyzer,
        velocity_monitor: GraphVelocityMonitor,
    ) -> None:
        self.graph = graph
        self.analyzer = analyzer
        self.velocity_monitor = velocity_monitor
        self.relationship_analyzer = RelationshipAnalyzer(graph)

    def analyze(
        self,
        transaction: Transaction,
        sender_id: str,
        receiver_id: str,
        vulnerability_scores: dict[str, float],
    ) -> dict[str, Any]:
        """Produce structural context for the orchestrator."""
        structural_signals: list[str] = []
        elevated = False

        # 1. Fan-in check on receiver
        fan_in = self.analyzer.detect_fan_in(receiver_id, window_hours=24, sender_threshold=3)
        if fan_in.get("is_fan_in"):
            structural_signals.append(
                f"Receiver has fan-in pattern: {fan_in['unique_senders']} unique senders in 24h"
            )
            elevated = True

        # 2. Fan-out check on sender
        fan_out = self.analyzer.detect_fan_out(sender_id, window_hours=24, receiver_threshold=3)
        if fan_out.get("is_fan_out"):
            structural_signals.append(
                f"Sender has fan-out pattern: {fan_out['unique_receivers']} unique receivers in 24h"
            )
            elevated = True

        # 3. Shared identity check on receiver
        shared = self.analyzer.detect_shared_identity(receiver_id)
        if shared:
            total_others = sum(len(s["other_accounts"]) for s in shared)
            structural_signals.append(
                f"Receiver shares device/IP with {total_others} other account(s)"
            )
            elevated = True

        # 4. Hub check on receiver
        hubs = self.analyzer.detect_hubs(time_window_hours=24, in_degree_threshold=3)
        if any(h["node_id"] == receiver_id for h in hubs):
            hub = next(h for h in hubs if h["node_id"] == receiver_id)
            structural_signals.append(
                f"Receiver is a hub: {hub['unique_senders']} unique senders in 24h"
            )
            elevated = True

        # 5. Velocity check on receiver
        receiver_velocity = self.velocity_monitor.compute_deviation(receiver_id, window_hours=24)
        velocity_deviation = receiver_velocity.deviation_ratio

        if velocity_deviation > 3.0:
            structural_signals.append(
                f"Receiver velocity spike: {velocity_deviation:.1f}x above baseline"
            )
            elevated = True

        # 6. Velocity check on sender (optional amplification)
        sender_velocity = self.velocity_monitor.compute_deviation(sender_id, window_hours=24)
        if sender_velocity.deviation_ratio > 3.0:
            structural_signals.append(
                f"Sender velocity spike: {sender_velocity.deviation_ratio:.1f}x above baseline"
            )
            elevated = True
            velocity_deviation = max(velocity_deviation, sender_velocity.deviation_ratio)

        # 7. Vulnerability amplification
        sender_vuln = vulnerability_scores.get(sender_id, 0.0)
        if sender_vuln > 0.7 and elevated:
            structural_signals.append(
                f"Vulnerable sender (score={sender_vuln:.2f}) combined with structural anomaly"
            )

        # 8. Build context string
        context = "; ".join(structural_signals) if structural_signals else "No structural anomalies"

        return {
            "structural_signals": structural_signals,
            "elevated": elevated,
            "context": context,
            "velocity_deviation": velocity_deviation,
            "velocity_report": receiver_velocity.model_dump(),
            "fan_in": fan_in,
            "fan_out": fan_out,
            "shared_identity": shared,
            "hubs": [h for h in hubs if h["node_id"] in (sender_id, receiver_id)],
        }
