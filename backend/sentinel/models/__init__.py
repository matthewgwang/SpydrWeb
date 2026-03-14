"""SENTINEL shared data contracts.

All Pydantic models used across the system are re-exported here so that
other modules can do:

    from sentinel.models import Transaction, AccountProfile, LayerSignal
"""

from sentinel.models.account import (
    AccountProfile,
    BaselineStats,
    CommunicationFingerprint,
    RecipientRiskScore,
    VulnerabilityFactor,
    VulnerabilityScore,
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
    ExploitationTactic,
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
    InterventionRecommendation,
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
    "CommunicationFingerprint",
    "RecipientRiskScore",
    "VulnerabilityFactor",
    "VulnerabilityScore",
    # graph
    "BrainOverlay",
    "EdgeType",
    "GraphContext",
    "GraphEdge",
    "GraphNode",
    "NodeType",
    "VelocityReport",
    # layers
    "ExploitationTactic",
    "FraudType",
    "LayerResult",
    "LayerSignal",
    "TestPlan",
    # report
    "Action",
    "AlertBundle",
    "CaseReport",
    "EvidenceBrief",
    "InterventionRecommendation",
    "TimelineEntry",
]
