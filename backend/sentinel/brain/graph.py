"""Brain Graph — NetworkX wrapper for the SENTINEL relationship map."""

from __future__ import annotations

from datetime import datetime

import networkx as nx


class BrainGraph:
    """MultiDiGraph of accounts, devices, merchants, IPs and their relationships."""

    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    # ── Node / Edge mutations ──────────────────────────────────────────

    def add_node(self, node_id: str, node_type: str = "account", **kwargs) -> None:
        self.graph.add_node(node_id, node_type=node_type, **kwargs)

    def add_edge(
        self, source: str, target: str, edge_type: str = "TRANSACTION", **kwargs
    ) -> None:
        if source not in self.graph:
            self.graph.add_node(source)
        if target not in self.graph:
            self.graph.add_node(target)
        self.graph.add_edge(source, target, edge_type=edge_type, **kwargs)

    def add_transaction_edge(self, sender_id: str, receiver_id: str, transaction) -> None:
        self.add_edge(
            sender_id,
            receiver_id,
            edge_type="TRANSACTION",
            amount=transaction.amount,
            timestamp=transaction.timestamp,
            step=transaction.step,
            tx_id=transaction.id,
        )

    # ── Queries ────────────────────────────────────────────────────────

    def get_subgraph(self, entity_id: str, depth: int = 2) -> dict:
        """BFS neighbourhood around a node."""
        if entity_id not in self.graph:
            return {"nodes": [], "edges": []}

        visited = {entity_id}
        frontier = {entity_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                for neighbor in set(self.graph.successors(node)) | set(
                    self.graph.predecessors(node)
                ):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier

        return self._serialize_nodes(visited)

    def get_node_info(self, entity_id: str) -> dict:
        if entity_id not in self.graph:
            return {}
        data = dict(self.graph.nodes[entity_id])
        in_edges = list(self.graph.in_edges(entity_id, data=True))
        out_edges = list(self.graph.out_edges(entity_id, data=True))
        return {
            "node": data,
            "in_degree": len(in_edges),
            "out_degree": len(out_edges),
            "in_edges": [{"from": e[0], **e[2]} for e in in_edges],
            "out_edges": [{"to": e[1], **e[2]} for e in out_edges],
        }

    def quick_check(self, sender_id: str, receiver_id: str) -> list[dict]:
        """Fast structural check for the fast-path filter."""
        anomalies: list[dict] = []
        if receiver_id in self.graph:
            in_degree = self.graph.in_degree(receiver_id)
            if in_degree > 10:
                anomalies.append(
                    {"suspicious": True, "reason": f"Receiver has high in-degree: {in_degree}"}
                )
        if receiver_id not in self.graph:
            anomalies.append({"suspicious": False, "reason": "Receiver is new to the graph"})
        return anomalies

    # ── Serialization for frontend (d3-force) ─────────────────────────

    def serialize_for_frontend(self) -> dict:
        return self._serialize_nodes(set(self.graph.nodes()))

    def _serialize_nodes(self, node_ids: set[str]) -> dict:
        nodes = []
        for node_id in node_ids:
            data = self.graph.nodes.get(node_id, {})
            nodes.append(
                {
                    "id": node_id,
                    "type": data.get("node_type", "account"),
                    "label": data.get("name", node_id),
                    "vulnerable": data.get("vulnerable", False),
                    "flagged": data.get("flagged", False),
                    **{
                        k: v
                        for k, v in data.items()
                        if k not in ("node_type", "name", "vulnerable", "flagged")
                        and isinstance(v, (str, int, float, bool))
                    },
                }
            )

        edges = []
        for u, v, data in self.graph.edges(data=True):
            if u in node_ids and v in node_ids:
                edge: dict = {
                    "source": u,
                    "target": v,
                    "type": data.get("edge_type", "TRANSACTION"),
                    "flagged": data.get("flagged", False),
                    "new": data.get("new", False),
                }
                if "amount" in data:
                    edge["amount"] = data["amount"]
                if "timestamp" in data and isinstance(data["timestamp"], datetime):
                    edge["timestamp"] = data["timestamp"].isoformat()
                edges.append(edge)

        return {"nodes": nodes, "edges": edges}
