"""FastAPI application factory with lifespan-managed services."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup, cleanup on shutdown."""

    from app.accounts.baselines import BaselineComputer
    from app.accounts.profile_builder import ProfileBuilder
    from app.accounts.recipient_scoring import RecipientScorer
    from app.accounts.store import AccountStore
    from app.accounts.vulnerability import VulnerabilityScorer
    from app.ai.cache import ResponseCache
    from app.ai.gpt_oss_provider import GPTOSSProvider
    from app.brain.analysis import GraphAnalyzer
    from app.brain.graph import BrainGraph
    from app.brain.overlay import BrainOverlayEngine
    from app.brain.velocity import GraphVelocityMonitor
    from app.core.alert_manager import AlertManager
    from app.core.event_stream import EventStream
    from app.core.fast_path import FastPathFilter
    from app.core.orchestrator import PipelineOrchestrator
    from app.core.scoring import ScoreComputer
    from app.data.generator import WorldStateBuilder
    from app.feedback.loop import FeedbackStore
    from app.layers.comprehension import ComprehensionLayer
    from app.layers.graph_layer import GraphLayer
    from app.layers.profiling import ProfilingLayer
    from app.layers.rules import RulesLayer
    from app.layers.synthesis import SynthesisLayer

    # Core infrastructure
    event_stream = EventStream()
    brain_graph = BrainGraph()
    llm_provider = GPTOSSProvider()
    response_cache = ResponseCache()

    # Brain analysis (shared by Layer 3 and BrainOverlay)
    graph_analyzer = GraphAnalyzer(brain_graph)
    velocity_monitor = GraphVelocityMonitor(brain_graph)

    # Account services
    account_store = AccountStore()
    baseline_computer = BaselineComputer(decay_factor=settings.BASELINE_DECAY_FACTOR)
    vulnerability_scorer = VulnerabilityScorer()
    recipient_scorer = RecipientScorer()
    profile_builder = ProfileBuilder(llm_provider=llm_provider, cache=response_cache)

    # Detection layers [L1, L2, L3, L4, L5]
    layer_1 = RulesLayer()
    layer_2 = ProfilingLayer(
        baseline_computer=baseline_computer,
        event_stream=event_stream,
    )
    layer_3 = GraphLayer(
        graph=brain_graph,
        analyzer=graph_analyzer,
        velocity_monitor=velocity_monitor,
    )
    layer_4 = ComprehensionLayer(
        llm_provider=llm_provider,
        cache=response_cache,
        event_stream=event_stream,
    )
    layer_5 = SynthesisLayer(llm_provider=llm_provider, cache=response_cache)
    layers = [layer_1, layer_2, layer_3, layer_4, layer_5]

    # Brain overlay (Step 7 structural context)
    brain_overlay = BrainOverlayEngine(
        graph=brain_graph,
        analyzer=graph_analyzer,
        velocity_monitor=velocity_monitor,
    )

    # Pipeline services
    fast_path = FastPathFilter()
    score_computer = ScoreComputer()
    alert_manager = AlertManager()
    feedback_store = FeedbackStore()

    # Orchestrator
    orchestrator = PipelineOrchestrator(
        event_stream=event_stream,
        account_store=account_store,
        profile_builder=profile_builder,
        vulnerability_scorer=vulnerability_scorer,
        recipient_scorer=recipient_scorer,
        brain_graph=brain_graph,
        brain_overlay=brain_overlay,
        layers=layers,
        fast_path=fast_path,
        score_computer=score_computer,
        alert_manager=alert_manager,
        llm_provider=llm_provider,
        cache=response_cache,
    )

    # World state builder (Phase 2 data)
    world_builder = WorldStateBuilder(
        event_stream=event_stream,
        account_store=account_store,
        brain_graph=brain_graph,
        baseline_computer=baseline_computer,
        profile_builder=profile_builder,
        vulnerability_scorer=vulnerability_scorer,
    )
    await world_builder.build()

    # Store references on app.state for routes
    app.state.event_stream = event_stream
    app.state.orchestrator = orchestrator
    app.state.account_store = account_store
    app.state.brain_graph = brain_graph
    app.state.alert_manager = alert_manager
    app.state.feedback_store = feedback_store
    app.state.world_builder = world_builder

    yield


def create_app() -> FastAPI:
    app = FastAPI(title="SENTINEL", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.CORS_ORIGIN],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    from app.api.routes import accounts, demo, feedback, graph, reports, transactions

    app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(graph.router, prefix="/graph", tags=["graph"])
    app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
    app.include_router(demo.router, prefix="/demo", tags=["demo"])

    from app.api.websocket import setup_websocket

    setup_websocket(app)

    return app
