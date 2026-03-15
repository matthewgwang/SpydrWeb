from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/{account_id}/profile")
async def get_profile(account_id: str, request: Request):
    store = request.app.state.account_store
    profile = store.get_profile(account_id)
    if not profile:
        return {"error": "Account not found"}
    return profile.model_dump()


@router.get("/")
async def list_accounts(request: Request):
    store = request.app.state.account_store
    return [p.model_dump() for p in store.get_all_profiles()]
