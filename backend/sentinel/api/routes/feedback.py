from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class FeedbackRequest(BaseModel):
    report_id: str
    action: str
    fraud_type: str = ""
    notes: str = ""


@router.post("/")
async def submit_feedback(feedback: FeedbackRequest, request: Request):
    store = request.app.state.feedback_store
    store.record(feedback.report_id, feedback.action, feedback.fraud_type, feedback.notes)
    return {"status": "recorded"}
