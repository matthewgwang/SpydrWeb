"""Graph pattern analysis — detect fraud-associated topologies in the Brain graph.

Pure Python, no AI. Operates on BrainGraph's underlying NetworkX MultiDiGraph.

Patterns detected:
  1. Hub detection     — nodes with abnormally high inbound connections
  2. Edge burst        — sudden spike in edges at a node
  3. Shared identity   — multiple accounts using the same device or IP
  4. Fan-out           — one account distributing to many receivers
  5. Fan-in            — many accounts sending to one receiver
  6. Temporal clustering — synchronized transactions across accounts
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.brain.graph import BrainGraph


class GraphAnalyzer:
    """Structural pattern detector on the SENTINEL Brain graph."""

    def __init__(self, graph: BrainGraph) -> None:
        self.graph = graph

    # ── Helpers ────────────────────────────────────────────────────────

    def _get_edges_since(self, cutoff: datetime) -> list[tuple[str, str, dict]]:
        """All graph edges with a timestamp >= cutoff."""
        results: list[tuple[str, str, dict]] = []
        for u, v, data in self.graph.graph.edges(data=True):
            ts = data.get("timestamp")
            if ts and isinstance(ts, datetime) and ts >= cutoff:
                results.append((u, v, data))
        return results

    def _get_node_edges_since(
        self,
        entity_id: str,
        cutoff: datetime,
        direction: str = "both",
    ) -> list[tuple[str, str, dict]]:
        """Edges connected to a specific node since cutoff.

        direction: "in", "out", or "both".
        """
        if entity_id not in self.graph.graph:
            return []

        edges: list[tuple[str, str, dict]] = []

        if direction in ("in", "both"):
            for u, v, data in self.graph.graph.in_edges(entity_id, data=True):
                ts = data.get("timestamp")
                if ts and isinstance(ts, datetime) and ts >= cutoff:
                    edges.append((u, v, data))

        if direction in ("out", "both"):
            for u, v, data in self.graph.graph.out_edges(entity_id, data=True):
                ts = data.get("timestamp")
                if ts and isinstance(ts, datetime) and ts >= cutoff:
                    edges.append((u, v, data))

        return edges

    def _get_all_node_edges(
        self, entity_id: str
    ) -> list[tuple[str, str, dict]]:
        """All in + out edges for a node (no time filter)."""
        if entity_id not in self.graph.graph:
            return []
        edges: list[tuple[str, str, dict]] = []
        edges.extend(self.graph.graph.in_edges(entity_id, data=True))
        edges.extend(self.graph.graph.out_edges(entity_id, data=True))
        return edges

    # ── Pattern 1: Hub Detection ──────────────────────────────────────

    def detect_hubs(
        self,
        time_window_hours: int = 24,
        in_degree_threshold: int = 5,
    ) -> list[dict]:
        """Find nodes with high recent inbound connections.

        Returns nodes whose unique inbound sender count in the time window
        exceeds in_degree_threshold.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=time_window_hours)
        recent_edges = self._get_edges_since(cutoff)

        inbound: dict[str, set[str]] = defaultdict(set)
        inbound_count: dict[str, int] = defaultdict(int)
        inbound_amount: dict[str, float] = defaultdict(float)

        for u, v, data in recent_edges:
            if data.get("edge_type") == "TRANSACTION":
                inbound[v].add(u)
                inbound_count[v] += 1
                inbound_amount[v] += data.get("amount", 0.0)

        hubs: list[dict] = []
        for node_id, senders in inbound.items():
            if len(senders) >= in_degree_threshold:
                hubs.append({
                    "node_id": node_id,
                    "unique_senders": len(senders),
                    "total_inbound_edges": inbound_count[node_id],
                    "total_inbound_amount": inbound_amount[node_id],
                    "time_window_hours": time_window_hours,
                    "reason": f"High inbound hub: {len(senders)} unique senders in {time_window_hours}h",
                })

        hubs.sort(key=lambda h: h["unique_senders"], reverse=True)
        return hubs

    # ── Pattern 2: Edge Burst Detection ───────────────────────────────

    def detect_edge_burst(
        self,
        entity_id: str,
        window_hours: int = 1,
        burst_ratio_threshold: float = 3.0,
    ) -> dict:
        """Detect sudden spike in edge activity at a node.

        Compares edges in the recent window to the node's historical average.
        """
        if entity_id not in self.graph.graph:
            return {
                "entity_id": entity_id,
                "recent_edge_count": 0,
                "window_hours": window_hours,
                "historical_avg_per_hour": 0.0,
                "burst_ratio": 0.0,
                "is_burst": False,
            }

        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        recent = self._get_node_edges_since(entity_id, cutoff)
        all_edges = self._get_all_node_edges(entity_id)

        timestamps = [
            data.get("timestamp")
            for _, _, data in all_edges
            if data.get("timestamp") and isinstance(data["timestamp"], datetime)
        ]

        if len(timestamps) < 2:
            return {
                "entity_id": entity_id,
                "recent_edge_count": len(recent),
                "window_hours": window_hours,
                "historical_avg_per_hour": 0.0,
                "burst_ratio": 0.0,
                "is_burst": False,
            }

        earliest = min(timestamps)
        latest = max(timestamps)
        history_hours = max((latest - earliest).total_seconds() / 3600, 1.0)
        historical_avg = len(all_edges) / history_hours

        recent_rate = len(recent) / max(window_hours, 0.01)
        burst_ratio = recent_rate / max(historical_avg, 0.01)

        return {
            "entity_id": entity_id,
            "recent_edge_count": len(recent),
            "window_hours": window_hours,
            "historical_avg_per_hour": round(historical_avg, 2),
            "burst_ratio": round(burst_ratio, 2),
            "is_burst": burst_ratio >= burst_ratio_threshold,
        }

    # ── Pattern 3: Shared Identity Detection ──────────────────────────

    def detect_shared_identity(self, entity_id: str) -> list[dict]:
        """Find other accounts sharing a device or IP with entity_id.

        Looks for USES_DEVICE and LOGGED_FROM edges, then finds other accounts
        connected to the same device/IP nodes.
        """
        if entity_id not in self.graph.graph:
            return []

        shared_types = {"USES_DEVICE", "LOGGED_FROM"}
        shared_nodes: list[tuple[str, str]] = []

        for _, target, data in self.graph.graph.out_edges(entity_id, data=True):
            if data.get("edge_type") in shared_types:
                shared_nodes.append((target, data["edge_type"]))

        for source, _, data in self.graph.graph.in_edges(entity_id, data=True):
            if data.get("edge_type") in shared_types:
                shared_nodes.append((source, data["edge_type"]))

        results: list[dict] = []
        seen_shared: set[str] = set()

        for shared_node, shared_type in shared_nodes:
            if shared_node in seen_shared:
                continue
            seen_shared.add(shared_node)

            other_accounts: set[str] = set()

            for neighbor in self.graph.graph.predecessors(shared_node):
                if neighbor != entity_id:
                    other_accounts.add(neighbor)
            for neighbor in self.graph.graph.successors(shared_node):
                if neighbor != entity_id:
                    other_accounts.add(neighbor)

            if other_accounts:
                results.append({
                    "shared_node": shared_node,
                    "shared_type": shared_type,
                    "other_accounts": sorted(other_accounts),
                })

        return results

    # ── Pattern 4: Fan-Out Detection ──────────────────────────────────

    def detect_fan_out(
        self,
        entity_id: str,
        window_hours: int = 24,
        receiver_threshold: int = 5,
    ) -> dict:
        """Detect one account distributing funds to many receivers.

        Classic mule distribution pattern.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        recent_out = self._get_node_edges_since(entity_id, cutoff, direction="out")

        unique_receivers: set[str] = set()
        total_amount = 0.0

        for _, v, data in recent_out:
            if data.get("edge_type") == "TRANSACTION":
                unique_receivers.add(v)
                total_amount += data.get("amount", 0.0)

        is_fan_out = len(unique_receivers) >= receiver_threshold

        return {
            "entity_id": entity_id,
            "unique_receivers": len(unique_receivers),
            "receiver_ids": sorted(unique_receivers),
            "total_amount": round(total_amount, 2),
            "window_hours": window_hours,
            "is_fan_out": is_fan_out,
        }

    # ── Pattern 5: Fan-In Detection ───────────────────────────────────

    def detect_fan_in(
        self,
        entity_id: str,
        window_hours: int = 24,
        sender_threshold: int = 5,
    ) -> dict:
        """Detect many accounts sending to one receiver.

        Collection point or mule endpoint pattern.
        """
        cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
        recent_in = self._get_node_edges_since(entity_id, cutoff, direction="in")

        unique_senders: set[str] = set()
        total_amount = 0.0

        for u, _, data in recent_in:
            if data.get("edge_type") == "TRANSACTION":
                unique_senders.add(u)
                total_amount += data.get("amount", 0.0)

        is_fan_in = len(unique_senders) >= sender_threshold

        return {
            "entity_id": entity_id,
            "unique_senders": len(unique_senders),
            "sender_ids": sorted(unique_senders),
            "total_amount": round(total_amount, 2),
            "window_hours": window_hours,
            "is_fan_in": is_fan_in,
        }

    # ── Pattern 6: Temporal Clustering ────────────────────────────────

    def detect_temporal_clustering(
        self,
        entity_ids: list[str],
        window_minutes: int = 30,
    ) -> dict:
        """Detect synchronized transaction timing across multiple accounts.

        If many of the given accounts transacted within a tight time window,
        it suggests coordination (e.g. mule network doing synchronized transfers).
        """
        if len(entity_ids) < 2:
            return {
                "entity_ids": entity_ids,
                "window_minutes": window_minutes,
                "is_clustered": False,
                "clustered_accounts": [],
                "cluster_window": None,
            }

        latest_txns: dict[str, datetime] = {}
        for eid in entity_ids:
            out_edges = list(self.graph.graph.out_edges(eid, data=True))
            in_edges = list(self.graph.graph.in_edges(eid, data=True))

            txn_timestamps: list[datetime] = []
            for _, _, data in out_edges + in_edges:
                ts = data.get("timestamp")
                if ts and isinstance(ts, datetime) and data.get("edge_type") == "TRANSACTION":
                    txn_timestamps.append(ts)

            if txn_timestamps:
                latest_txns[eid] = max(txn_timestamps)

        if len(latest_txns) < 2:
            return {
                "entity_ids": entity_ids,
                "window_minutes": window_minutes,
                "is_clustered": False,
                "clustered_accounts": [],
                "cluster_window": None,
            }

        sorted_times = sorted(latest_txns.items(), key=lambda x: x[1])
        threshold = timedelta(minutes=window_minutes)

        best_cluster: list[str] = []
        for i, (eid_i, ts_i) in enumerate(sorted_times):
            cluster = [eid_i]
            for j in range(i + 1, len(sorted_times)):
                eid_j, ts_j = sorted_times[j]
                if ts_j - ts_i <= threshold:
                    cluster.append(eid_j)
                else:
                    break
            if len(cluster) > len(best_cluster):
                best_cluster = cluster

        is_clustered = len(best_cluster) >= 3 or (
            len(best_cluster) >= 2 and len(entity_ids) == 2
        )

        cluster_start = latest_txns.get(best_cluster[0]) if best_cluster else None
        cluster_end = latest_txns.get(best_cluster[-1]) if best_cluster else None

        return {
            "entity_ids": entity_ids,
            "window_minutes": window_minutes,
            "is_clustered": is_clustered,
            "clustered_accounts": best_cluster,
            "clustered_count": len(best_cluster),
            "total_accounts": len(entity_ids),
            "cluster_window": {
                "start": cluster_start.isoformat() if cluster_start else None,
                "end": cluster_end.isoformat() if cluster_end else None,
            },
        }
