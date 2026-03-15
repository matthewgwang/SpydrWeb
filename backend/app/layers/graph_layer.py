"""Layer 3 — Graph topology and velocity analysis.

Uses GraphAnalyzer and GraphVelocityMonitor to detect structural fraud patterns
around the sender and receiver of a transaction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.layers.base import DetectionLayer
from app.models.layers import LayerSignal

if TYPE_CHECKING:
    from app.brain.analysis import GraphAnalyzer
    from app.brain.graph import BrainGraph
    from app.brain.velocity import GraphVelocityMonitor
    from app.core.event_stream import EventStream
    from app.models.account import AccountProfile
    from app.models.transaction import Transaction


class GraphLayer(DetectionLayer):
    """Layer 3 — graph topology + velocity detection."""

    layer_id = 3
    layer_name = "graph"

    def __init__(
        self,
        graph: BrainGraph,
        analyzer: GraphAnalyzer,
        velocity_monitor: GraphVelocityMonitor,
    ) -> None:
        self.graph = graph
        self.analyzer = analyzer
        self.velocity_monitor = velocity_monitor

    async def analyze(
        self,
        transaction: Transaction,
        sender: AccountProfile,
        receiver: AccountProfile,
        event_stream: EventStream,
        graph: BrainGraph,
    ) -> LayerSignal:
        """Run graph analysis on sender and receiver, return combined signal."""
        findings: list[str] = []
        max_confidence = 0.0
        evidence: dict = {}

        sender_id = transaction.sender_id
        receiver_id = transaction.receiver_id
        window_hours = 24

        # 1. Hub check on receiver
        hubs = self.analyzer.detect_hubs(
            time_window_hours=window_hours,
            in_degree_threshold=3,
        )
        receiver_hub = next((h for h in hubs if h["node_id"] == receiver_id), None)
        if receiver_hub:
            findings.append(
                f"Receiver is hub: {receiver_hub['unique_senders']} unique senders in {window_hours}h"
            )
            max_confidence = max(max_confidence, 0.85)
            evidence["receiver_hub"] = receiver_hub

        # 2. Fan-in on receiver
        fan_in = self.analyzer.detect_fan_in(
            receiver_id,
            window_hours=window_hours,
            sender_threshold=3,
        )
        if fan_in.get("is_fan_in"):
            findings.append(
                f"Receiver fan-in: {fan_in['unique_senders']} unique senders, ${fan_in['total_amount']:,.0f} in {window_hours}h"
            )
            max_confidence = max(max_confidence, 0.8)
            evidence["receiver_fan_in"] = fan_in

        # 3. Fan-out on sender
        fan_out = self.analyzer.detect_fan_out(
            sender_id,
            window_hours=window_hours,
            receiver_threshold=3,
        )
        if fan_out.get("is_fan_out"):
            findings.append(
                f"Sender fan-out: {fan_out['unique_receivers']} unique receivers, ${fan_out['total_amount']:,.0f} in {window_hours}h"
            )
            max_confidence = max(max_confidence, 0.8)
            evidence["sender_fan_out"] = fan_out

        # 4. Shared identity on receiver
        shared = self.analyzer.detect_shared_identity(receiver_id)
        if shared:
            total_others = sum(len(s["other_accounts"]) for s in shared)
            findings.append(
                f"Receiver shares device/IP with {total_others} other account(s)"
            )
            max_confidence = max(max_confidence, 0.9)
            evidence["shared_identity"] = [s["shared_node"] for s in shared]

        # 5. Velocity on receiver
        receiver_velocity = self.velocity_monitor.compute_deviation(
            receiver_id,
            window_hours=window_hours,
        )
        if receiver_velocity.deviation_ratio > 3.0:
            findings.append(
                f"Receiver velocity spike: {receiver_velocity.deviation_ratio:.1f}x above baseline"
            )
            max_confidence = max(max_confidence, 0.75)
            evidence["receiver_velocity"] = receiver_velocity.model_dump()

        # 6. Velocity on sender
        sender_velocity = self.velocity_monitor.compute_deviation(
            sender_id,
            window_hours=window_hours,
        )
        if sender_velocity.deviation_ratio > 3.0:
            findings.append(
                f"Sender velocity spike: {sender_velocity.deviation_ratio:.1f}x above baseline"
            )
            max_confidence = max(max_confidence, 0.75)
            evidence["sender_velocity"] = sender_velocity.model_dump()

        triggered = len(findings) > 0
        explanation = "; ".join(findings) if findings else "No graph anomalies detected"

        return LayerSignal(
            layer_id=self.layer_id,
            layer_name=self.layer_name,
            triggered=triggered,
            confidence=max_confidence,
            explanation=explanation,
            evidence=evidence,
            severity="high" if max_confidence >= 0.85 else ("medium" if triggered else "low"),
        )
