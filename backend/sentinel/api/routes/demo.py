from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/start")
async def start_demo(request: Request):
    """Initialize world state and begin normal transaction replay."""
    return {
        "status": "ready",
        "accounts": len(request.app.state.account_store.get_all_profiles()),
    }


@router.post("/inject-fraud/{scenario_name}")
async def inject_fraud(scenario_name: str, request: Request):
    """Inject a fraud scenario and process the fraudulent transaction."""
    world_builder = request.app.state.world_builder
    orchestrator = request.app.state.orchestrator

    fraud_tx = await world_builder.inject_scenario(scenario_name)
    report = await orchestrator.process(fraud_tx)

    return {
        "transaction": fraud_tx.model_dump(),
        "report": report.model_dump(),
    }
