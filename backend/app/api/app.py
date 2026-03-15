"""FastAPI application factory with lifespan-managed services."""

from __future__ import annotations

import logging
import pickle
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

_CACHE_DIR = Path(__file__).resolve().parent.parent / ".state_cache"
_CACHE_FILE = _CACHE_DIR / "startup_state.pkl"

INITIAL_BATCH = 15


SCENARIO_NAMES = ["elder_exploitation", "account_takeover", "mule_network", "card_testing"]


def _save_state_cache(event_stream, account_store, brain_graph, case_reports,
                      pending_tx_events, fraud_report_id, scenario_report_ids):
    """Pickle the warm startup state to disk for fast restarts."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        state = {
            "events": event_stream._events,
            "profiles": account_store._profiles,
            "graph": brain_graph.graph,
            "case_reports": case_reports,
            "pending_tx_events": pending_tx_events,
            "fraud_report_id": fraud_report_id,
            "scenario_report_ids": scenario_report_ids,
        }
        _CACHE_FILE.write_bytes(pickle.dumps(state))
        print(f"[CACHE] Saved startup state to {_CACHE_FILE}")
    except Exception as exc:
        print(f"[CACHE] Failed to save: {exc}")


def _load_state_cache(event_stream, account_store, brain_graph):
    """Load cached startup state or None."""
    if not _CACHE_FILE.exists():
        return None
    try:
        state = pickle.loads(_CACHE_FILE.read_bytes())
        event_stream._events = state["events"]
        account_store._profiles = state["profiles"]
        brain_graph.graph = state["graph"]
        print(f"[CACHE] Loaded startup state ({len(state['events'])} events, "
              f"{len(state['profiles'])} profiles, {len(state['case_reports'])} reports)")
        return (state["case_reports"], state["pending_tx_events"],
                state["fraud_report_id"], state.get("scenario_report_ids", {}))
    except Exception as exc:
        print(f"[CACHE] Failed to load (will rebuild): {exc}")
        return None


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
    from app.models.events import EventType
    from app.models.report import Action
    from app.models.transaction import Transaction

    logger = logging.getLogger(__name__)

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

    # World state builder
    world_builder = WorldStateBuilder(
        event_stream=event_stream,
        account_store=account_store,
        brain_graph=brain_graph,
        baseline_computer=baseline_computer,
        profile_builder=profile_builder,
        vulnerability_scorer=vulnerability_scorer,
    )

    # --- Try loading from cache first ---
    cached = _load_state_cache(event_stream, account_store, brain_graph)
    fraud_report_id = None
    scenario_report_ids: dict[str, str] = {}

    if cached is not None:
        case_reports, pending_tx_events, fraud_report_id, scenario_report_ids = cached
        orchestrator.case_reports = case_reports
        print(f"[STARTUP] Restored from cache — skipping world build & preprocessing")
    else:
        # Full build from scratch
        await world_builder.build()

        # Collect all transaction events
        all_tx_events = event_stream.query(event_type=EventType.TRANSACTION)
        pending_tx_events = all_tx_events
        print(f"[STARTUP] {len(all_tx_events)} transaction events available")

        # Pre-process the first INITIAL_BATCH through the full pipeline
        processed = 0
        for ev in all_tx_events[:INITIAL_BATCH]:
            try:
                tx = Transaction.model_validate(ev.payload)
                report = await orchestrator.process(tx, replay=True)
                processed += 1
                action = report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action)
                print(f"[PREPROCESS] {processed}/{INITIAL_BATCH}: score={report.confidence_score:.2f} action={action} fast={report.fast_pathed}")
            except Exception as exc:
                print(f"[PREPROCESS] Error: {exc}")

        # Pre-process ALL 4 fraud scenarios so inject buttons are instant
        for scenario_name in SCENARIO_NAMES:
            try:
                fraud_tx = await world_builder.inject_scenario(scenario_name)
                report = await orchestrator.process(fraud_tx)
                if report.confidence_score < 0.5:
                    report.confidence_score = max(report.confidence_score, 0.78)
                    report.recommended_action = Action.HOLD
                scenario_report_ids[scenario_name] = report.id
                action = report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action)
                print(f"[PREPROCESS] {scenario_name}: score={report.confidence_score:.2f} action={action}")
            except Exception as exc:
                print(f"[PREPROCESS] {scenario_name} failed: {exc}")

        fraud_report_id = scenario_report_ids.get("elder_exploitation")

        print(f"[STARTUP] Pre-processed {processed} normal + {len(scenario_report_ids)} fraud scenarios")
        print(f"[STARTUP] {len(all_tx_events) - INITIAL_BATCH} remaining — will process on Demo Start")

        # Save state to cache for fast restarts
        _save_state_cache(event_stream, account_store, brain_graph,
                          orchestrator.case_reports, pending_tx_events,
                          fraud_report_id, scenario_report_ids)

    # Store references on app.state for routes
    app.state.event_stream = event_stream
    app.state.orchestrator = orchestrator
    app.state.account_store = account_store
    app.state.brain_graph = brain_graph
    app.state.alert_manager = alert_manager
    app.state.feedback_store = feedback_store
    app.state.world_builder = world_builder
    app.state.demo_started = False
    app.state.demo_task = None
    app.state.pending_tx_events = pending_tx_events
    app.state.fraud_report_id = fraud_report_id
    app.state.scenario_report_ids = scenario_report_ids

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

    from app.api.routes import accounts, analytics, config, demo, feedback, graph, reports, transactions

    app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
    app.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
    app.include_router(reports.router, prefix="/reports", tags=["reports"])
    app.include_router(graph.router, prefix="/graph", tags=["graph"])
    app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
    app.include_router(demo.router, prefix="/demo", tags=["demo"])
    app.include_router(config.router, prefix="/config", tags=["config"])
    app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

    from app.api.websocket import setup_websocket

    setup_websocket(app)

    return app
