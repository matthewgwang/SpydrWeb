from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/by-transaction/{tx_id}")
async def get_report_by_transaction(tx_id: str, request: Request):
    orchestrator = request.app.state.orchestrator
    report = orchestrator.get_report_by_transaction(tx_id)
    if not report:
        return {"error": "Report not found for this transaction"}
    return report.model_dump()


@router.get("/{report_id}")
async def get_report(report_id: str, request: Request):
    orchestrator = request.app.state.orchestrator
    report = orchestrator.get_report(report_id)
    if not report:
        return {"error": "Report not found"}
    return report.model_dump()


@router.get("/")
async def list_reports(request: Request, limit: int = 20):
    orchestrator = request.app.state.orchestrator
    reports = orchestrator.get_recent_reports(limit)
    return [r.model_dump() for r in reports]
