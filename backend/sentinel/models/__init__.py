"""SENTINEL shared data contracts.

All Pydantic models used across the system are re-exported here so that
other modules can do:

    from sentinel.models import Transaction, AccountProfile, LayerSignal
"""

from sentinel.models.account import (
    AccountProfile,
    BaselineStats,
    ProfileSummary,
    RecipientRiskScore,
)
from sentinel.models.events import Event, EventType
from sentinel.models.graph_models import (
    BrainOverlay,
    EdgeType,
    GraphContext,
    GraphEdge,
    GraphNode,
    NodeType,
    VelocityReport,
)
from sentinel.models.layers import (
    FraudType,
    LayerResult,
    LayerSignal,
    TestPlan,
)
from sentinel.models.report import (
    Action,
    AlertBundle,
    CaseReport,
    EvidenceBrief,
    TimelineEntry,
)
from sentinel.models.transaction import Transaction, TransactionContext, TransactionType

__all__ = [
    # events
    "Event",
    "EventType",
    # transaction
    "Transaction",
    "TransactionContext",
    "TransactionType",
    # account
    "AccountProfile",
    "BaselineStats",
    "ProfileSummary",
    "RecipientRiskScore",
    # graph
    "BrainOverlay",
    "EdgeType",
    "GraphContext",
    "GraphEdge",
    "GraphNode",
    "NodeType",
    "VelocityReport",
    # layers
    "FraudType",
    "LayerResult",
    "LayerSignal",
    "TestPlan",
    # report
    "Action",
    "AlertBundle",
    "CaseReport",
    "EvidenceBrief",
    "TimelineEntry",
]
