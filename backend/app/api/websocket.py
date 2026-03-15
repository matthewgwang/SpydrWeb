"""WebSocket feed — streams transactions and fraud alerts to the frontend."""

from __future__ import annotations

import asyncio
import hashlib
import logging

from fastapi import WebSocket, WebSocketDisconnect

from app.config import settings

logger = logging.getLogger(__name__)

_FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Charles", "Lisa", "Daniel", "Nancy", "Matthew", "Betty", "Anthony",
    "Sandra", "Mark", "Ashley", "Donald", "Kimberly", "Steven", "Emily",
    "Andrew", "Donna", "Paul", "Michelle", "Joshua", "Carol",
    "Kenneth", "Amanda", "Kevin", "Dorothy", "Brian", "Melissa",
    "George", "Deborah", "Timothy", "Stephanie",
]

_LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell",
    "Mitchell", "Carter", "Roberts",
]

_name_cache: dict[str, str] = {}


def _generate_name(account_id: str) -> str:
    """Deterministically generate a realistic name from an account ID."""
    if account_id in _name_cache:
        return _name_cache[account_id]

    h = int(hashlib.md5(account_id.encode()).hexdigest(), 16)

    if account_id.startswith("M"):
        merchants = [
            "QuickMart", "FreshGrocer", "CityGas", "Metro Pharmacy", "Daily Brew",
            "TopShelf Liquor", "GreenLeaf Market", "SunMart", "ValueStop",
            "Corner Deli", "PrimeCuts Butcher", "TechZone", "BookNook",
            "StyleHouse", "PetWorld", "AutoParts Plus", "HomeDepot",
            "CostSaver", "FoodBarn", "WellnessCo",
        ]
        name = merchants[h % len(merchants)]
    else:
        first = _FIRST_NAMES[h % len(_FIRST_NAMES)]
        last = _LAST_NAMES[(h >> 8) % len(_LAST_NAMES)]
        name = f"{first} {last}"

    _name_cache[account_id] = name
    return name


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


def _resolve_name(account_store, account_id: str) -> str:
    """Look up a human-readable name for an account ID, falling back to generated names."""
    if not account_id:
        return ""
    profile = account_store.get_profile(account_id)
    if profile and profile.name:
        return profile.name
    return _generate_name(account_id)


def _build_tx_message(event, account_store, orchestrator) -> dict:
    """Build a transaction message dict from an event."""
    payload = event.payload
    sender_id = payload.get("sender_id", "") or event.account_id
    receiver_id = payload.get("receiver_id", "")
    tx_id = payload.get("id", event.id)

    report = orchestrator.get_report_by_transaction(tx_id)
    if report:
        status = report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action)
        confidence = report.confidence_score
        report_id = report.id
    else:
        status = "pending"
        confidence = 0.0
        report_id = None

    merchant = payload.get("merchant_category", "")
    tx_type = merchant if merchant else payload.get("type", "")

    return {
        "id": tx_id,
        "step": event.step,
        "timestamp": str(event.timestamp),
        "sender_id": sender_id,
        "sender_name": _resolve_name(account_store, sender_id),
        "receiver_id": receiver_id,
        "receiver_name": _resolve_name(account_store, receiver_id),
        "amount": payload.get("amount", 0),
        "tx_type": tx_type,
        "status": status,
        "confidence_score": confidence,
        "report_id": report_id,
    }


def setup_websocket(app):
    @app.websocket("/ws/feed")
    async def transaction_feed(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            event_stream = app.state.event_stream
            account_store = app.state.account_store
            orchestrator = app.state.orchestrator

            # No initial batch — table starts empty.
            # Transactions appear only after Demo Start via broadcast.

            # Keep connection alive, waiting for broadcasts
            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            manager.disconnect(websocket)

    async def broadcast_alert(report):
        """Called after fraud processing to push both the transaction and alert to all clients."""
        tx = report.transaction
        account_store = app.state.account_store

        merchant = ""
        if tx and tx.description:
            merchant = tx.description

        await manager.broadcast(
            {
                "type": "transaction",
                "data": {
                    "id": tx.id if tx else report.transaction_id,
                    "step": tx.step if tx else 0,
                    "timestamp": str(tx.timestamp) if tx else str(report.timestamp),
                    "sender_id": tx.sender_id if tx else "",
                    "sender_name": report.sender_profile.name if report.sender_profile else "",
                    "receiver_id": tx.receiver_id if tx else "",
                    "receiver_name": report.receiver_profile.name if report.receiver_profile else "",
                    "amount": tx.amount if tx else 0,
                    "tx_type": merchant or (tx.type.value if tx else ""),
                    "status": report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action),
                    "confidence_score": report.confidence_score,
                    "report_id": report.id,
                },
            }
        )

        if report.confidence_score >= 0.3:
            await manager.broadcast(
                {
                    "type": "alert",
                    "data": {
                        "id": report.id,
                        "transaction_id": report.transaction_id,
                        "timestamp": str(report.timestamp),
                        "sender_name": report.sender_profile.name if report.sender_profile else "",
                        "receiver_name": report.receiver_profile.name if report.receiver_profile else "",
                        "amount": report.transaction.amount if report.transaction else 0,
                        "confidence_score": report.confidence_score,
                        "exploitation_tactic": (
                            report.evidence_brief.exploitation_tactic.value
                            if report.evidence_brief
                            else "unknown"
                        ),
                        "recommended_action": report.recommended_action.value if hasattr(report.recommended_action, "value") else str(report.recommended_action),
                        "summary": (
                            report.evidence_brief.narrative[:200]
                            if report.evidence_brief
                            else ""
                        ),
                    },
                }
            )

    app.state.broadcast_alert = broadcast_alert
