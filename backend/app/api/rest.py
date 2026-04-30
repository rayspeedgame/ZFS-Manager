from __future__ import annotations

from fastapi import APIRouter

from app.core.state import state_store
from app.schemas.zfs_state import AppState


router = APIRouter(prefix="/api", tags=["state"])


@router.get("/state", response_model=AppState)
async def get_state() -> AppState:
    """Return the latest in-memory snapshot used by the frontend."""
    return await state_store.get_state()


@router.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
