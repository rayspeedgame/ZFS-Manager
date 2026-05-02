from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.state import state_store
from app.runtime import config, poller, pool_property_updater
from app.schemas.property_update import PoolPropertyUpdateRequest, PoolPropertyUpdateResponse
from app.schemas.zfs_state import AppState


router = APIRouter(prefix="/api", tags=["state"])


@router.get("/state", response_model=AppState)
async def get_state() -> AppState:
    """Return the latest in-memory snapshot used by the frontend."""
    return await state_store.get_state()


@router.post(
    "/pools/{pool_name}/properties",
    response_model=PoolPropertyUpdateResponse,
    tags=["pools"],
)
async def update_pool_properties(
    pool_name: str,
    payload: PoolPropertyUpdateRequest,
) -> PoolPropertyUpdateResponse:
    if config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool property updates require SSH mode.")

    if not payload.changes:
        raise HTTPException(status_code=400, detail="No property changes were provided.")

    results = await pool_property_updater.apply_pool_changes(pool=pool_name, changes=payload.changes)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Force a fresh SSH read so the UI sees the real post-write state.
        await poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return PoolPropertyUpdateResponse(
        pool=pool_name,
        results=results,
        refreshed=refreshed,
        refresh_error=refresh_error,
    )


@router.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
