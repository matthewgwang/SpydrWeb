"""FastAPI application factory with lifespan-managed services."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sentinel.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all services on startup, cleanup on shutdown."""

    from sentinel.accounts.baselines import BaselineComputer
    from sentinel.accounts.profile_builder import ProfileBuilder
    from sentinel.accounts.recipient_scoring import RecipientScorer
    from sentinel.accounts.store import AccountStore
    from sentinel.accounts.vulnerability import VulnerabilityScorer
    from sentinel.ai.cache import ResponseCache
    from sentinel.ai.gpt_oss_provider import GPTOSSProvider
    from sentinel.brain.graph import BrainGraph
    from sentinel.core.alert_manager import AlertManager
    from sentinel.core.event_stream import EventStream
    from sentinel.core.fast_path import FastPathFilter
    from sentinel.core.orchestrator import PipelineOrchestrator
    from sentinel.core.scoring import ScoreComputer
    from sentinel.data.generator import WorldStateBuilder
    from sentinel.feedback.loop import FeedbackStore

    # Core infrastructure
    event_stream = EventStream()
    brain_graph = BrainGraph()
    llm_provider = GPTOSSProvider()
    response_cache = ResponseCache()

    # Account services
    account_store = AccountStore()
    baseline_computer = BaselineComputer(decay_factor=settings.BASELINE_DECAY_FACTOR)
    vulnerability_scorer = VulnerabilityScorer()
    recipient_scorer = RecipientScorer()
    profile_builder = ProfileBuilder(llm_provider=llm_provider, cache=response_cache)

    # Pipeline services
    fast_path = FastPathFilter()
    score_computer = ScoreComputer()
    alert_manager = AlertManager()
    feedback_store = FeedbackStore()

    # Detection layers (stubs — real implementations come in Phase 1)
    layers: list = []

    # Orchestrator
    orchestrator = PipelineOrchestrator(
        event_stream=event_stream,
        account_store=account_store,
        profile_builder=profile_builder,
        vulnerability_scorer=vulnerability_scorer,
        recipient_scorer=recipient_scorer,
        brain_graph=brain_graph,
        brain_overlay=brain_graph,  # placeholder until BrainOverlay built
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

    from sentinel.api.routes import accounts, demo, feedback, graph, reports, transactions

    app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(graph.router, prefix="/graph", tags=["graph"])
    app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
    app.include_router(demo.router, prefix="/demo", tags=["demo"])

    from sentinel.api.websocket import setup_websocket

    setup_websocket(app)

    return app
