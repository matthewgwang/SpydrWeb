from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    ACCOUNT = "ACCOUNT"
    DEVICE = "DEVICE"
    MERCHANT = "MERCHANT"
    PAYEE = "PAYEE"
    IP = "IP"


class EdgeType(str, Enum):
    TRANSACTION = "TRANSACTION"
    USES_DEVICE = "USES_DEVICE"
    SHOPS_AT = "SHOPS_AT"
    PAYS_TO = "PAYS_TO"
    LOGGED_FROM = "LOGGED_FROM"


class GraphNode(BaseModel):
    id: str
    node_type: NodeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphContext(BaseModel):
    """Subgraph neighbourhood returned by the Brain for a specific entity."""
    center_node: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    depth: int = 1


class VelocityReport(BaseModel):
    """Output of graph velocity monitoring (brain/velocity.py)."""
    entity_id: str
    current_velocity: float = 0.0       # new edges per hour in window
    baseline_velocity: float = 0.0      # historical average edges per hour
    deviation_ratio: float = 0.0        # current / baseline
    time_window_hours: int = 24


class BrainOverlay(BaseModel):
    """Structural context produced by brain/overlay.py (Step 5/6)."""
    structural_signals: list[str] = Field(default_factory=list)
    elevated: bool = False
    context: str = ""
    velocity: Optional[VelocityReport] = None
