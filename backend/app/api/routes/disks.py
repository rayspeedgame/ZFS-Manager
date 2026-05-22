from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app import runtime
from app.core.auth import require_authenticated_request
from app.core.config import save_config
from app.core.state import state_store
from app.schemas.disk_label import DiskLabelUpdateRequest, DiskLabelUpdateResponse

router = APIRouter(prefix="/api")


@router.put("/disks/{disk_key}/label", response_model=DiskLabelUpdateResponse, tags=["disks"])
async def update_disk_label(
    disk_key: str,
    payload: DiskLabelUpdateRequest,
    request: Request,
) -> DiskLabelUpdateResponse:
    require_authenticated_request(request)

    state = await state_store.get_state()
    disk = next((item for item in (state.data.disks or []) if str(item.get("diskKey") or "") == disk_key), None)
    if disk is None:
        raise HTTPException(status_code=404, detail=f"Disk {disk_key!r} was not found in the latest snapshot.")

    if payload.label:
        runtime.config.disk_labels[disk_key] = payload.label
    else:
        runtime.config.disk_labels.pop(disk_key, None)

    save_config(runtime.config)
    await runtime.poller.refresh_once(force_all=True)
    return DiskLabelUpdateResponse(
        disk_key=disk_key,
        label=payload.label,
        refreshed=True,
        message="Disk label saved and state refreshed.",
    )
