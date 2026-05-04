from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.auth import (
    auth_is_enabled,
    clear_auth_cookie,
    require_authenticated_request,
    request_is_authenticated,
    set_auth_cookie,
)
from app.core.state import state_store
from app.core.config import AppConfig, save_config
from app import runtime
from app.schemas.auth import AuthStatusResponse, LoginRequest, LoginResponse
from app.schemas.dataset_create import DatasetCreateRequest, DatasetCreateResponse
from app.schemas.dataset_destroy import DatasetDestroyResponse
from app.schemas.dataset_property_update import DatasetPropertyUpdateRequest, DatasetPropertyUpdateResponse
from app.schemas.pool_create import PoolCreateRequest, PoolCreateResponse
from app.schemas.pool_destroy import PoolDestroyResponse
from app.schemas.pool_remove import PoolRemoveRequest, PoolRemoveResponse
from app.schemas.property_update import PoolPropertyUpdateRequest, PoolPropertyUpdateResponse
from app.schemas.settings import SettingsSaveResponse
from app.schemas.ssh_test import SSHConnectionTestRequest, SSHConnectionTestResponse
from app.schemas.topology_update import PoolTopologyUpdateRequest, PoolTopologyUpdateResponse
from app.schemas.zfs_state import AppState
from app.ssh.client import SSHClient, SSHConfig


router = APIRouter(prefix="/api", tags=["state"])

DATASET_EDITABLE_PROPERTIES = {
    "filesystem": {
        "aclinherit",
        "aclmode",
        "acltype",
        "atime",
        "canmount",
        "checksum",
        "compression",
        "copies",
        "dedup",
        "devices",
        "dnodesize",
        "exec",
        "logbias",
        "mountpoint",
        "nbmand",
        "overlay",
        "primarycache",
        "quota",
        "readonly",
        "recordsize",
        "redundant_metadata",
        "refquota",
        "refreservation",
        "relatime",
        "reservation",
        "secondarycache",
        "setuid",
        "snapdir",
        "sync",
        "xattr",
    },
    "volume": {
        "checksum",
        "compression",
        "copies",
        "dedup",
        "logbias",
        "primarycache",
        "readonly",
        "refreservation",
        "reservation",
        "secondarycache",
        "snapdev",
        "sync",
        "volmode",
        "volsize",
    },
    "snapshot": set(),
}

DATASET_CREATE_ALLOWED_PROPERTIES = {
    "filesystem": {
        "aclinherit",
        "aclmode",
        "acltype",
        "atime",
        "canmount",
        "casesensitivity",
        "checksum",
        "compression",
        "copies",
        "dedup",
        "devices",
        "dnodesize",
        "exec",
        "logbias",
        "mountpoint",
        "nbmand",
        "normalization",
        "overlay",
        "primarycache",
        "quota",
        "readonly",
        "recordsize",
        "redundant_metadata",
        "refquota",
        "refreservation",
        "relatime",
        "reservation",
        "secondarycache",
        "setuid",
        "snapdir",
        "sync",
        "utf8only",
        "xattr",
    },
    "volume": {
        "checksum",
        "compression",
        "copies",
        "dedup",
        "logbias",
        "primarycache",
        "readonly",
        "refreservation",
        "reservation",
        "secondarycache",
        "snapdev",
        "sync",
        "volblocksize",
        "volmode",
        "volsize",
    },
}


@router.get("/state", response_model=AppState)
async def get_state(request: Request) -> AppState:
    """Return the latest in-memory snapshot used by the frontend."""
    require_authenticated_request(request)
    return await state_store.get_state()


@router.post("/state/refresh", response_model=AppState, tags=["system"])
async def force_refresh_state(request: Request) -> AppState:
    """Force a full backend refresh instead of only returning cached state."""
    require_authenticated_request(request)
    return await runtime.poller.refresh_once(force_all=True)


@router.get("/auth/status", response_model=AuthStatusResponse, tags=["auth"])
async def get_auth_status(request: Request) -> AuthStatusResponse:
    return AuthStatusResponse(
        enabled=auth_is_enabled(),
        authenticated=request_is_authenticated(request),
    )


@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
async def login(payload: LoginRequest, response: Response) -> LoginResponse:
    if not auth_is_enabled():
        return LoginResponse(success=True, message="Authentication is disabled.")

    if payload.password != (runtime.config.auth.password or ""):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    set_auth_cookie(response)
    return LoginResponse(success=True, message="Login succeeded.")


@router.post("/auth/logout", response_model=LoginResponse, tags=["auth"])
async def logout(response: Response) -> LoginResponse:
    clear_auth_cookie(response)
    return LoginResponse(success=True, message="Logged out.")


@router.get("/settings", response_model=AppConfig, tags=["system"])
async def get_settings(request: Request) -> AppConfig:
    """Return the currently active backend configuration."""
    require_authenticated_request(request)
    return runtime.config.model_copy(deep=True)


@router.put("/settings", response_model=SettingsSaveResponse, tags=["system"])
async def save_settings(payload: AppConfig, request: Request, response: Response) -> SettingsSaveResponse:
    """Persist backend settings and reload long-lived runtime services."""
    require_authenticated_request(request)
    if payload.auth.enabled and not (payload.auth.password or "").strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login password is required when password login is enabled.",
        )
    config_path = save_config(payload)
    next_config = await runtime.reload_runtime(payload)
    if next_config.auth.enabled and (next_config.auth.password or "").strip():
        set_auth_cookie(response)
    else:
        clear_auth_cookie(response)
    return SettingsSaveResponse(
        config=next_config,
        config_path=str(config_path),
        reloaded=True,
        message="Settings saved and runtime reloaded.",
    )


@router.post("/settings/test-ssh", response_model=SSHConnectionTestResponse, tags=["system"])
async def test_ssh_connection(payload: SSHConnectionTestRequest, request: Request) -> SSHConnectionTestResponse:
    """Test SSH connectivity with the provided settings without saving them."""
    require_authenticated_request(request)
    client = SSHClient(
        SSHConfig(
            host=payload.ssh.host,
            username=payload.ssh.username,
            port=payload.ssh.port,
            password=payload.ssh.password,
            known_hosts=payload.ssh.known_hosts,
            client_keys=payload.ssh.key_files,
            connect_timeout=payload.ssh.connect_timeout,
            keepalive_interval=payload.ssh.keepalive_interval,
            keepalive_count_max=payload.ssh.keepalive_count_max,
        )
    )

    try:
        await client.connect()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"SSH connection test failed: {exc}") from exc
    finally:
        await client.close()

    return SSHConnectionTestResponse(
        success=True,
        message="SSH connection succeeded.",
    )


@router.post(
    "/pools",
    response_model=PoolCreateResponse,
    tags=["pools"],
)
async def create_pool(payload: PoolCreateRequest) -> PoolCreateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool creation requires SSH mode.")

    state = await state_store.get_state()
    _validate_pool_creation(payload=payload, state=state)

    result = await runtime.pool_creator.create_pool(payload)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Pool writes always force a full refresh so the response reflects
        # the host's real post-command state instead of local assumptions.
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return result.model_copy(update={"refreshed": refreshed, "refresh_error": refresh_error})


@router.post(
    "/datasets",
    response_model=DatasetCreateResponse,
    tags=["datasets"],
)
async def create_dataset(payload: DatasetCreateRequest) -> DatasetCreateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset creation requires SSH mode.")

    state = await state_store.get_state()
    _validate_dataset_creation(payload=payload, state=state)

    result = await runtime.dataset_creator.create_dataset(payload)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return result.model_copy(update={"refreshed": refreshed, "refresh_error": refresh_error})


@router.post(
    "/datasets/{dataset_name:path}/destroy",
    response_model=DatasetDestroyResponse,
    tags=["datasets"],
)
async def destroy_dataset(dataset_name: str) -> DatasetDestroyResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset destroy requires SSH mode.")

    state = await state_store.get_state()
    dataset = _require_dataset(dataset_name=dataset_name, state=state)
    _validate_dataset_destroy(dataset=dataset)

    result = await runtime.dataset_destroyer.destroy_dataset(dataset_name)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
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
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool destroy requires SSH mode.")

    state = await state_store.get_state()
    _require_pool(pool_name=pool_name, state=state)

    result = await runtime.pool_destroyer.destroy_pool(pool_name)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
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
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology removal requires SSH mode.")

    state = await state_store.get_state()
    target = _validate_pool_removal(pool_name=pool_name, payload=payload, state=state)

    result = await runtime.pool_remover.remove_target(
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
        await runtime.poller.refresh_once(force_all=True)
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
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool property updates require SSH mode.")

    if not payload.changes:
        raise HTTPException(status_code=400, detail="No property changes were provided.")

    results = await runtime.pool_property_updater.apply_pool_changes(pool=pool_name, changes=payload.changes)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Force a fresh SSH read so the UI sees the real post-write state.
        await runtime.poller.refresh_once(force_all=True)
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
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology updates require SSH mode.")

    if not payload.additions:
        raise HTTPException(status_code=400, detail="No topology additions were provided.")

    state = await state_store.get_state()
    _validate_topology_additions(pool_name=pool_name, payload=payload, state=state)

    results = await runtime.pool_topology_updater.apply_pool_additions(
        pool=pool_name,
        additions=payload.additions,
        force=payload.force,
    )

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return PoolTopologyUpdateResponse(
        pool=pool_name,
        results=results,
        refreshed=refreshed,
        refresh_error=refresh_error,
    )


@router.post(
    "/datasets/{dataset_name:path}/properties",
    response_model=DatasetPropertyUpdateResponse,
    tags=["datasets"],
)
async def update_dataset_properties(
    dataset_name: str,
    payload: DatasetPropertyUpdateRequest,
) -> DatasetPropertyUpdateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset property updates require SSH mode.")

    if not payload.changes:
        raise HTTPException(status_code=400, detail="No property changes were provided.")

    state = await state_store.get_state()
    dataset = _require_dataset(dataset_name=dataset_name, state=state)
    _validate_dataset_property_changes(dataset=dataset, payload=payload)

    results = await runtime.dataset_property_updater.apply_dataset_changes(dataset=dataset_name, changes=payload.changes)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    return DatasetPropertyUpdateResponse(
        dataset=dataset_name,
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


def _require_dataset(*, dataset_name: str, state: AppState) -> dict:
    datasets = state.data.datasets or []
    dataset = next((item for item in datasets if item.get("name") == dataset_name), None)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_name!r} was not found in the latest snapshot.")
    return dataset


def _validate_dataset_property_changes(
    *,
    dataset: dict,
    payload: DatasetPropertyUpdateRequest,
) -> None:
    dataset_type = str(dataset.get("type") or "unknown")
    allowed = DATASET_EDITABLE_PROPERTIES.get(dataset_type, set())
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Dataset type {dataset_type!r} does not support property editing in this version.",
        )

    unsupported = sorted(
        {
            str(change.property)
            for change in payload.changes
            if str(change.property) not in allowed
        }
    )
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported dataset properties for type {dataset_type!r}: "
                f"{', '.join(unsupported)}"
            ),
        )


def _validate_dataset_creation(*, payload: DatasetCreateRequest, state: AppState) -> None:
    datasets = state.data.datasets or []
    parent = next((item for item in datasets if item.get("name") == payload.parent), None)
    if parent is None:
        raise HTTPException(status_code=404, detail=f"Parent dataset {payload.parent!r} was not found in the latest snapshot.")

    parent_type = str(parent.get("type") or "unknown")
    if parent_type != "filesystem":
        raise HTTPException(
            status_code=400,
            detail=f"Parent {payload.parent!r} must be a filesystem dataset.",
        )

    full_name = payload.full_name
    if any(dataset.get("name") == full_name for dataset in datasets):
        raise HTTPException(status_code=400, detail=f"Dataset {full_name!r} already exists.")

    allowed = DATASET_CREATE_ALLOWED_PROPERTIES[payload.type]
    unsupported = sorted(
        {
            str(property_item.name)
            for property_item in payload.properties
            if str(property_item.name) not in allowed
        }
    )
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported create properties for type {payload.type!r}: {', '.join(unsupported)}",
        )


def _validate_dataset_destroy(*, dataset: dict) -> None:
    dataset_name = str(dataset.get("name") or "")
    pool_name = str(dataset.get("poolName") or "")
    if dataset_name and pool_name and dataset_name == pool_name:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Dataset {dataset_name!r} is the root dataset for pool {pool_name!r}. "
                "Use pool destroy from the Pools view for that operation."
            ),
        )


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

    allowed_root_properties = DATASET_CREATE_ALLOWED_PROPERTIES["filesystem"]
    unsupported_root_properties = sorted(
        {
            str(property_item.name)
            for property_item in payload.root_dataset_properties
            if str(property_item.name) not in allowed_root_properties
        }
    )
    if unsupported_root_properties:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported root dataset properties for pool creation: "
                f"{', '.join(unsupported_root_properties)}"
            ),
        )

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
