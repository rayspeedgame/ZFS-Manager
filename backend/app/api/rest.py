from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.state import state_store
from app.runtime import (
    config,
    poller,
    pool_creator,
    pool_destroyer,
    pool_property_updater,
    pool_remover,
    pool_topology_updater,
)
from app.schemas.pool_create import PoolCreateRequest, PoolCreateResponse
from app.schemas.pool_destroy import PoolDestroyResponse
from app.schemas.pool_remove import PoolRemoveRequest, PoolRemoveResponse
from app.schemas.property_update import PoolPropertyUpdateRequest, PoolPropertyUpdateResponse
from app.schemas.topology_update import PoolTopologyUpdateRequest, PoolTopologyUpdateResponse
from app.schemas.zfs_state import AppState


router = APIRouter(prefix="/api", tags=["state"])


@router.get("/state", response_model=AppState)
async def get_state() -> AppState:
    """Return the latest in-memory snapshot used by the frontend."""
    return await state_store.get_state()


@router.post(
    "/pools",
    response_model=PoolCreateResponse,
    tags=["pools"],
)
async def create_pool(payload: PoolCreateRequest) -> PoolCreateResponse:
    if config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool creation requires SSH mode.")

    state = await state_store.get_state()
    _validate_pool_creation(payload=payload, state=state)

    result = await pool_creator.create_pool(payload)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Pool writes always force a full refresh so the response reflects
        # the host's real post-command state instead of local assumptions.
        await poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return result.model_copy(update={"refreshed": refreshed, "refresh_error": refresh_error})


@router.post(
    "/pools/{pool_name}/destroy",
    response_model=PoolDestroyResponse,
    tags=["pools"],
)
async def destroy_pool(pool_name: str) -> PoolDestroyResponse:
    if config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool destroy requires SSH mode.")

    state = await state_store.get_state()
    _require_pool(pool_name=pool_name, state=state)

    result = await pool_destroyer.destroy_pool(pool_name)

    refreshed = False
    refresh_error: str | None = None
    try:
        await poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return result.model_copy(update={"refreshed": refreshed, "refresh_error": refresh_error})


@router.post(
    "/pools/{pool_name}/remove",
    response_model=PoolRemoveResponse,
    tags=["pools"],
)
async def remove_pool_target(
    pool_name: str,
    payload: PoolRemoveRequest,
) -> PoolRemoveResponse:
    if config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology removal requires SSH mode.")

    state = await state_store.get_state()
    target = _validate_pool_removal(pool_name=pool_name, payload=payload, state=state)

    result = await pool_remover.remove_target(
        pool=pool_name,
        command_target=payload.command_target,
        display_label=str(target.get("displayLabel") or payload.command_target),
        target_type=str(target.get("targetType") or "device"),
        vdev_class=str(target.get("vdevClass") or "data"),
        layout=str(target.get("layout") or "stripe"),
    )

    refreshed = False
    refresh_error: str | None = None
    try:
        await poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return result.model_copy(update={"refreshed": refreshed, "refresh_error": refresh_error})


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


@router.post(
    "/pools/{pool_name}/topology",
    response_model=PoolTopologyUpdateResponse,
    tags=["pools"],
)
async def update_pool_topology(
    pool_name: str,
    payload: PoolTopologyUpdateRequest,
) -> PoolTopologyUpdateResponse:
    if config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology updates require SSH mode.")

    if not payload.additions:
        raise HTTPException(status_code=400, detail="No topology additions were provided.")

    state = await state_store.get_state()
    _validate_topology_additions(pool_name=pool_name, payload=payload, state=state)

    results = await pool_topology_updater.apply_pool_additions(pool=pool_name, additions=payload.additions)

    refreshed = False
    refresh_error: str | None = None
    try:
        await poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return PoolTopologyUpdateResponse(
        pool=pool_name,
        results=results,
        refreshed=refreshed,
        refresh_error=refresh_error,
    )


@router.get("/health", tags=["system"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


def _validate_topology_additions(
    *,
    pool_name: str,
    payload: PoolTopologyUpdateRequest,
    state: AppState,
) -> None:
    pools = state.data.pools or []
    pool = next((item for item in pools if item.get("name") == pool_name), None)
    if pool is None:
        raise HTTPException(status_code=404, detail=f"Pool {pool_name!r} was not found in the latest snapshot.")

    candidate_devices = {
        str(device.get("path")): device
        for device in (pool.get("availableTopologyDevices") or [])
        if device.get("path")
    }

    for addition in payload.additions:
        if addition.category == "data":
            raise HTTPException(
                status_code=400,
                detail="Adding data vdevs is not supported in this version yet.",
            )
        for device_path in addition.devices:
            device = candidate_devices.get(device_path)
            if device is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Device {device_path!r} is not available for pool topology updates.",
                )


def _require_pool(*, pool_name: str, state: AppState) -> dict:
    pools = state.data.pools or []
    pool = next((item for item in pools if item.get("name") == pool_name), None)
    if pool is None:
        raise HTTPException(status_code=404, detail=f"Pool {pool_name!r} was not found in the latest snapshot.")
    return pool


def _validate_pool_removal(
    *,
    pool_name: str,
    payload: PoolRemoveRequest,
    state: AppState,
) -> dict:
    pool = _require_pool(pool_name=pool_name, state=state)
    # The frontend only receives targets that the backend already classified as
    # removable, so REST validation just needs to re-check against that list.
    targets = pool.get("removalTargets") or []
    target = next((item for item in targets if item.get("commandTarget") == payload.command_target), None)
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"Target {payload.command_target!r} is not removable in the latest snapshot.",
        )
    return target


def _validate_pool_creation(*, payload: PoolCreateRequest, state: AppState) -> None:
    pools = state.data.pools or []
    if any(pool.get("name") == payload.name for pool in pools):
        raise HTTPException(status_code=400, detail=f"Pool {payload.name!r} already exists.")

    disks = state.data.disks or []
    candidate_devices = {
        str(device.get("path")): device
        for device in disks
        if _disk_is_available_for_creation(device)
    }

    selected_devices: set[str] = set()
    for vdev in payload.vdevs:
        for device_path in vdev.devices:
            if device_path in selected_devices:
                raise HTTPException(status_code=400, detail=f"Device {device_path!r} was selected more than once.")
            device = candidate_devices.get(device_path)
            if device is None:
                raise HTTPException(status_code=400, detail=f"Device {device_path!r} is not available for pool creation.")
            selected_devices.add(device_path)


def _disk_is_available_for_creation(disk: dict) -> bool:
    if disk.get("poolName") and disk.get("poolName") != "-":
        return False
    filesystem = str(disk.get("filesystem") or "-").lower()
    if not _is_reusable_filesystem(filesystem, disk.get("poolName")):
        return False
    for partition in disk.get("partitions", []):
        if partition.get("poolName") and partition.get("poolName") != "-":
            return False
        partition_filesystem = str(partition.get("filesystem") or "-").lower()
        if not _is_reusable_filesystem(partition_filesystem, partition.get("poolName")):
            return False
    return True


def _is_reusable_filesystem(filesystem: str | None, pool_name: str | None) -> bool:
    normalized_fs = str(filesystem or "-").lower()
    normalized_pool = str(pool_name or "-")
    if normalized_fs in {"-", "", "none", "unknown"}:
        return True
    # Destroyed pools often leave a ZFS label behind. We still expose that to
    # the UI, but treat it as reusable when the device no longer belongs to an
    # active pool.
    if normalized_fs == "zfs_member" and normalized_pool == "-":
        return True
    return False
