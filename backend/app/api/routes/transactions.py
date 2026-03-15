from fastapi import APIRouter, Request

from app.models.events import EventType
from app.models.transaction import Transaction

router = APIRouter()


@router.post("/process")
async def process_transaction(transaction: Transaction, request: Request):
    orchestrator = request.app.state.orchestrator
    report = await orchestrator.process(transaction)
    return report.model_dump()


@router.get("/")
async def list_transactions(request: Request, limit: int = 50):
    event_stream = request.app.state.event_stream
    tx_events = event_stream.query(event_type=EventType.TRANSACTION, limit=limit)
    return [e.payload for e in tx_events]
