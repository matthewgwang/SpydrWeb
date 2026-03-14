"""Graph velocity monitoring — track rate of graph change per node.

Compares recent edge activity to historical baseline. A node that normally
gets 1 edge per day but suddenly gets 10 in an hour is suspicious.

Output: VelocityReport (current_velocity, baseline_velocity, deviation_ratio).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sentinel.models.graph_models import VelocityReport

if TYPE_CHECKING:
    from sentinel.brain.graph import BrainGraph


class GraphVelocityMonitor:
    """Monitors edge rate per node and detects velocity spikes."""

    def __init__(self, graph: BrainGraph) -> None:
        self.graph = graph

    def _get_all_node_edges(self, entity_id: str) -> list[dict]:
        """All in+out edges for a node, each as a data dict."""
        if entity_id not in self.graph.graph:
            return []

        edges: list[dict] = []
        for item in self.graph.graph.in_edges(entity_id, data=True):
            data = item[-1] if isinstance(item[-1], dict) else {}
            edges.append(data)
        for item in self.graph.graph.out_edges(entity_id, data=True):
            data = item[-1] if isinstance(item[-1], dict) else {}
            edges.append(data)
        return edges

    def get_edge_velocity(
        self,
        entity_id: str,
        window_hours: int = 24,
        reference_time: datetime | None = None,
    ) -> float:
        """Edges per hour in the recent time window.

        reference_time: if None, uses datetime.utcnow().
        """
        ref = reference_time or datetime.utcnow()
        cutoff = ref - timedelta(hours=window_hours)

        all_data = self._get_all_node_edges(entity_id)
        count = 0
        for data in all_data:
            ts = data.get("timestamp")
            if ts and isinstance(ts, datetime) and ts >= cutoff:
                count += 1

        return count / max(window_hours, 0.01)

    def get_baseline_velocity(self, entity_id: str) -> float:
        """Average edges per hour over the entity's full history."""
        all_data = self._get_all_node_edges(entity_id)
        timestamps = [
            d.get("timestamp")
            for d in all_data
            if d.get("timestamp") and isinstance(d["timestamp"], datetime)
        ]

        if len(timestamps) < 2:
            return 0.1  # avoid division by zero, small default

        earliest = min(timestamps)
        latest = max(timestamps)
        span_hours = max((latest - earliest).total_seconds() / 3600, 0.1)
        return len(all_data) / span_hours

    def compute_deviation(
        self,
        entity_id: str,
        window_hours: int = 24,
        reference_time: datetime | None = None,
    ) -> VelocityReport:
        """Compare current velocity to baseline. Returns VelocityReport."""
        ref = reference_time or datetime.utcnow()
        current = self.get_edge_velocity(entity_id, window_hours, ref)
        baseline = self.get_baseline_velocity(entity_id)

        if baseline <= 0:
            baseline = 0.1
        deviation_ratio = current / baseline

        return VelocityReport(
            entity_id=entity_id,
            current_velocity=round(current, 4),
            baseline_velocity=round(baseline, 4),
            deviation_ratio=round(deviation_ratio, 4),
            time_window_hours=window_hours,
        )
