"""WebSocket feed — streams transactions and fraud alerts to the frontend."""

from __future__ import annotations

import asyncio

from fastapi import WebSocket, WebSocketDisconnect

from sentinel.config import settings


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


def setup_websocket(app):
    @app.websocket("/ws/feed")
    async def transaction_feed(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            event_stream = app.state.event_stream
            all_tx_events = [
                e
                for e in event_stream.get_all()
                if e.event_type.value == "transaction"
            ]

            for event in all_tx_events:
                payload = event.payload
                message = {
                    "type": "transaction",
                    "data": {
                        "id": event.id,
                        "step": event.step,
                        "timestamp": str(event.timestamp),
                        "sender_id": payload.get("sender_id", ""),
                        "receiver_id": payload.get("receiver_id", ""),
                        "amount": payload.get("amount", 0),
                        "tx_type": payload.get("type", ""),
                        "status": "cleared",
                        "confidence_score": 0.0,
                    },
                }
                await websocket.send_json(message)
                await asyncio.sleep(settings.DEMO_SPEED)

            while True:
                await websocket.receive_text()

        except WebSocketDisconnect:
            manager.disconnect(websocket)

    async def broadcast_alert(report):
        """Called by the orchestrator when a fraud alert is generated."""
        if report.confidence_score >= 0.3:
            await manager.broadcast(
                {
                    "type": "alert",
                    "data": {
                        "id": report.id,
                        "transaction_id": report.transaction_id,
                        "sender_name": report.sender_profile.name,
                        "receiver_name": report.receiver_profile.name,
                        "amount": report.transaction.amount,
                        "confidence_score": report.confidence_score,
                        "exploitation_tactic": (
                            report.evidence_brief.exploitation_tactic.value
                            if report.evidence_brief
                            else "unknown"
                        ),
                        "recommended_action": report.recommended_action.value,
                        "summary": (
                            report.evidence_brief.narrative[:200]
                            if report.evidence_brief
                            else ""
                        ),
                    },
                }
            )

    app.state.broadcast_alert = broadcast_alert
