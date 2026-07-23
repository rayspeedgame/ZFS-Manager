from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app import runtime
from app.core.auth import require_authenticated_request
from app.core.config import save_config
from app.core.state import state_store
from app.schemas.disk_label import DiskLabelUpdateRequest, DiskLabelUpdateResponse

router = APIRouter(prefix="/api")


def _find_disk_in_state(disk_key: str, state) -> dict | None:
    """Look up a disk row by diskKey, kernelPath, or diskPath."""
    for item in state.data.disks or []:
        if str(item.get("diskKey") or "") == disk_key:
            return item
        if str(item.get("kernelPath") or "") == disk_key:
            return item
        if str(item.get("path") or "") == disk_key:
            return item
    return None


def _match_smart_device_path(disk: dict) -> str | None:
    """Return the best device path for SMART lookup from a disk row."""
    for candidate in ("kernelPath", "path", "diskPath", "byIdPath"):
        value = disk.get(candidate)
        if value:
            return str(value)
    return None


@router.put("/disks/{disk_key}/label", response_model=DiskLabelUpdateResponse, tags=["disks"])
async def update_disk_label(
    disk_key: str,
    payload: DiskLabelUpdateRequest,
    request: Request,
) -> DiskLabelUpdateResponse:
    require_authenticated_request(request)

    state = await state_store.get_state()
    disk = _find_disk_in_state(disk_key, state)
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


@router.get("/disks/{disk_key}/smart", tags=["disks"])
async def get_disk_smart(disk_key: str, request: Request) -> dict:
    """Return cached SMART data for a specific disk."""
    require_authenticated_request(request)

    state = await state_store.get_state()
    disk = _find_disk_in_state(disk_key, state)
    if disk is None:
        raise HTTPException(status_code=404, detail=f"Disk {disk_key!r} was not found in the latest snapshot.")

    smart_overview = state.data.smart_overview
    if smart_overview is None:
        return {
            "device_path": _match_smart_device_path(disk) or disk_key,
            "raw_data_available": False,
            "error": "SMART data has not been collected yet.",
        }

    dev_path = _match_smart_device_path(disk) or disk_key
    smart_info = smart_overview.devices.get(dev_path)

    if smart_info is None:
        return {
            "device_path": dev_path,
            "raw_data_available": False,
            "error": "No SMART data available for this device.",
        }

    return smart_info.model_dump(mode="json")


@router.post("/disks/{disk_key}/smart/refresh", tags=["disks"])
async def refresh_disk_smart(disk_key: str, request: Request) -> dict:
    """Force refresh all SMART data."""
    require_authenticated_request(request)

    if runtime.poller._config.poller.mode == "fixture":
        raise HTTPException(status_code=400, detail="SMART refresh is not available in fixture mode. Enable SSH mode first.")

    await runtime.poller.refresh_once(force_all=True)
    return await get_disk_smart(disk_key, request)
