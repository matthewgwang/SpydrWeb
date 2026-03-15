import asyncio
import logging

from fastapi import APIRouter, Request

from app.config import settings
from app.models.transaction import Transaction

router = APIRouter()
logger = logging.getLogger(__name__)

DEMO_STREAM_LIMIT = 50

# The Nth transaction in the demo stream will be the pre-computed fraud (1-indexed)
FRAUD_INSERT_POSITION = 4


async def _broadcast_fraud_report(app, broadcast_alert):
    """Broadcast the pre-computed fraud report at the configured demo position."""
    orchestrator = app.state.orchestrator
    fraud_report_id = getattr(app.state, "fraud_report_id", None)
    if not fraud_report_id:
        logger.warning("No pre-computed fraud report available")
        return

    report = orchestrator.get_report(fraud_report_id)
    if report and broadcast_alert:
        await broadcast_alert(report)
        action = report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action)
        logger.info(
            "Demo FRAUD at position %d: score=%.2f action=%s",
            FRAUD_INSERT_POSITION, report.confidence_score, action,
        )


async def _demo_stream_task(app):
    """Background task: stream pre-processed transactions, then process+stream remaining.

    Progress is saved on app.state so pause/resume picks up where it left off.
    """
    orchestrator = app.state.orchestrator
    broadcast_alert = getattr(app.state, "broadcast_alert", None)
    pending_events = getattr(app.state, "pending_tx_events", [])

    already_processed_ids = {r.transaction_id for r in orchestrator.case_reports}
    fraud_report_id = getattr(app.state, "fraud_report_id", None)
    fraud_tx_id = None
    if fraud_report_id:
        fraud_report = orchestrator.get_report(fraud_report_id)
        if fraud_report:
            fraud_tx_id = fraud_report.transaction_id

    # Resume from saved progress
    streamed_ids: set[str] = getattr(app.state, "_demo_streamed_ids", set())
    total_streamed: int = getattr(app.state, "_demo_total_streamed", 0)
    fraud_broadcast: bool = getattr(app.state, "_demo_fraud_done", False)

    # Phase 1: broadcast already-processed transactions one by one
    for ev in pending_events:
        if not app.state.demo_started:
            return

        tx_id = ev.payload.get("id", ev.id)
        if tx_id in streamed_ids:
            continue
        if tx_id not in already_processed_ids:
            continue
        if tx_id == fraud_tx_id:
            continue

        # Insert fraud report at the configured position
        if total_streamed == FRAUD_INSERT_POSITION - 1 and not fraud_broadcast:
            fraud_broadcast = True
            app.state._demo_fraud_done = True
            await _broadcast_fraud_report(app, broadcast_alert)
            total_streamed += 1
            app.state._demo_total_streamed = total_streamed
            await asyncio.sleep(settings.DEMO_SPEED)

        report = orchestrator.get_report_by_transaction(tx_id)
        if report and broadcast_alert:
            await broadcast_alert(report)
            streamed_ids.add(tx_id)
            total_streamed += 1
            app.state._demo_streamed_ids = streamed_ids
            app.state._demo_total_streamed = total_streamed
            await asyncio.sleep(settings.DEMO_SPEED)

    logger.info("Demo phase 1: streamed %d transactions", total_streamed)

    # Phase 2: process remaining transactions through full pipeline and broadcast
    unprocessed = [
        ev for ev in pending_events
        if ev.payload.get("id", ev.id) not in already_processed_ids
        and ev.payload.get("id", ev.id) not in streamed_ids
    ]

    remaining = min(len(unprocessed), DEMO_STREAM_LIMIT - total_streamed)
    for i, ev in enumerate(unprocessed[:max(remaining, 0)]):
        if not app.state.demo_started:
            break

        # Insert fraud at position if not yet done (in case Phase 1 had < 3 items)
        if total_streamed == FRAUD_INSERT_POSITION - 1 and not fraud_broadcast:
            fraud_broadcast = True
            app.state._demo_fraud_done = True
            await _broadcast_fraud_report(app, broadcast_alert)
            total_streamed += 1
            app.state._demo_total_streamed = total_streamed
            await asyncio.sleep(settings.DEMO_SPEED)

        tx_id = ev.payload.get("id", ev.id)
        try:
            tx = Transaction.model_validate(ev.payload)
            report = await orchestrator.process(tx, replay=True)
            if broadcast_alert:
                await broadcast_alert(report)
            action = report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action)
            logger.info(
                "Demo stream [%d]: score=%.2f action=%s",
                total_streamed + 1, report.confidence_score, action,
            )
        except Exception as exc:
            logger.warning("Demo stream error on event %d: %s", i, exc)
        streamed_ids.add(tx_id)
        total_streamed += 1
        app.state._demo_streamed_ids = streamed_ids
        app.state._demo_total_streamed = total_streamed
        await asyncio.sleep(settings.DEMO_SPEED)

    logger.info("Demo stream complete: %d total", total_streamed)


@router.post("/start")
async def start_demo(request: Request):
    """Start the demo: begin background processing and streaming of transactions."""
    app = request.app

    if app.state.demo_started:
        return {
            "status": "already_running",
            "reports": len(app.state.orchestrator.case_reports),
        }

    app.state.demo_started = True
    app.state.demo_task = asyncio.create_task(_demo_stream_task(app))

    return {
        "status": "started",
        "accounts": len(app.state.account_store.get_all_profiles()),
        "pre_processed": len(app.state.orchestrator.case_reports),
    }


@router.post("/pause")
async def pause_demo(request: Request):
    """Pause the demo stream. The background task will stop at its next iteration."""
    app = request.app

    if not app.state.demo_started:
        return {"status": "not_running"}

    app.state.demo_started = False

    task = getattr(app.state, "demo_task", None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    app.state.demo_task = None

    return {
        "status": "paused",
        "reports": len(app.state.orchestrator.case_reports),
    }


@router.post("/inject-fraud/{scenario_name}")
async def inject_fraud(scenario_name: str, request: Request):
    """Inject a fraud scenario — uses pre-computed report from cache if available."""
    orchestrator = request.app.state.orchestrator
    scenario_report_ids = getattr(request.app.state, "scenario_report_ids", {})
    broadcast_alert = getattr(request.app.state, "broadcast_alert", None)

    cached_id = scenario_report_ids.get(scenario_name)
    if cached_id:
        report = orchestrator.get_report(cached_id)
        if report:
            if broadcast_alert:
                await broadcast_alert(report)
            return {
                "transaction": report.transaction.model_dump() if report.transaction else {},
                "report": report.model_dump(),
            }

    # Fallback: process live if not cached
    world_builder = request.app.state.world_builder
    fraud_tx = await world_builder.inject_scenario(scenario_name)
    report = await orchestrator.process(fraud_tx)
    if broadcast_alert:
        await broadcast_alert(report)
    return {
        "transaction": fraud_tx.model_dump(),
        "report": report.model_dump(),
    }


@router.post("/clear-cache")
async def clear_cache():
    """Delete the startup state cache so the next restart rebuilds from scratch."""
    from app.api.app import _CACHE_FILE
    if _CACHE_FILE.exists():
        _CACHE_FILE.unlink()
        return {"status": "cleared"}
    return {"status": "no_cache"}
