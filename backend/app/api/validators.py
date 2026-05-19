from __future__ import annotations

from fastapi import HTTPException

from app import runtime
from app.api.constants import DATASET_CREATE_ALLOWED_PROPERTIES, DATASET_EDITABLE_PROPERTIES
from app.core.state import state_store
from app.schemas.dataset_create import DatasetCreateRequest
from app.schemas.dataset_property_update import DatasetPropertyUpdateRequest
from app.schemas.pool_create import PoolCreateRequest
from app.schemas.pool_remove import PoolRemoveRequest
from app.schemas.task_schedule import TaskScheduleCreateRequest, TaskScheduleUpdateRequest
from app.schemas.topology_update import PoolTopologyUpdateRequest
from app.schemas.zfs_state import AppState


def validate_topology_additions(
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


def require_pool(*, pool_name: str, state: AppState) -> dict:
    pools = state.data.pools or []
    pool = next((item for item in pools if item.get("name") == pool_name), None)
    if pool is None:
        raise HTTPException(status_code=404, detail=f"Pool {pool_name!r} was not found in the latest snapshot.")
    return pool


def pool_has_active_scrub(pool: dict) -> bool:
    scan_status = pool.get("scanStatus") or {}
    if scan_status.get("kind") == "scrub" and scan_status.get("active"):
        return True
    scan = str((pool.get("status") or {}).get("scan") or "").lower()
    return "scrub in progress" in scan


async def validate_task_schedule_payload(payload: TaskScheduleCreateRequest) -> None:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Task schedules require SSH mode.")
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="A schedule title is required.")
    if not payload.scope_name.strip():
        raise HTTPException(status_code=400, detail="A schedule scope name is required.")
    validate_schedule_pattern_fields(payload.schedule_type, payload.pattern)
    state = await state_store.get_state()
    if payload.kind == "pool.scrub.schedule":
        if payload.scope_type != "pool":
            raise HTTPException(status_code=400, detail="Scheduled scrub currently only supports pool scope.")
        if payload.schedule_type != "weekly":
            raise HTTPException(status_code=400, detail="Scheduled scrub currently only supports weekly recurrence.")
        require_pool(pool_name=payload.scope_name, state=state)
        return
    if payload.kind == "snapshot.schedule":
        if payload.scope_type != "dataset":
            raise HTTPException(status_code=400, detail="Scheduled snapshots currently only support dataset scope.")
        dataset = require_dataset(dataset_name=payload.scope_name, state=state)
        validate_snapshot_parent(dataset)
        validate_snapshot_schedule_metadata(payload.metadata)
        return
    raise HTTPException(status_code=400, detail=f"Unsupported schedule kind: {payload.kind!r}.")


async def validate_task_schedule_update(
    kind: str,
    scope_type: str,
    scope_name: str,
    schedule_type: str,
    payload: TaskScheduleUpdateRequest,
) -> None:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Task schedules require SSH mode.")
    state = await state_store.get_state()
    if kind == "pool.scrub.schedule":
        if scope_type != "pool":
            raise HTTPException(status_code=400, detail="Scheduled scrub currently only supports pool scope.")
        if not scope_name:
            raise HTTPException(status_code=400, detail="Schedule scope is missing a pool name.")
        require_pool(pool_name=scope_name, state=state)
    elif kind == "snapshot.schedule":
        if scope_type != "dataset":
            raise HTTPException(status_code=400, detail="Scheduled snapshots currently only support dataset scope.")
        if not scope_name:
            raise HTTPException(status_code=400, detail="Schedule scope is missing a dataset name.")
        dataset = require_dataset(dataset_name=scope_name, state=state)
        validate_snapshot_parent(dataset)
        if payload.metadata is not None:
            validate_snapshot_schedule_metadata(payload.metadata)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported schedule kind: {kind!r}.")
    if payload.pattern is None:
        return
    validate_schedule_pattern_fields(schedule_type, payload.pattern)


def validate_schedule_pattern_fields(schedule_type: str, pattern) -> None:
    normalized_type = str(schedule_type or "").lower()
    if normalized_type not in {"minutely", "hourly", "daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail=f"Unsupported schedule type: {schedule_type!r}.")
    if normalized_type == "minutely":
        if pattern.interval is None:
            raise HTTPException(status_code=400, detail="Minutely schedules require an interval.")
        return
    if normalized_type == "hourly":
        if pattern.interval is None:
            raise HTTPException(status_code=400, detail="Hourly schedules require an interval.")
        if pattern.minute is None:
            raise HTTPException(status_code=400, detail="Hourly schedules require a minute value.")
        return
    if normalized_type == "daily":
        if pattern.hour is None or pattern.minute is None:
            raise HTTPException(status_code=400, detail="Daily schedules require hour and minute values.")
        return
    if normalized_type == "weekly":
        if pattern.weekday is None or pattern.hour is None or pattern.minute is None:
            raise HTTPException(status_code=400, detail="Weekly schedules require weekday, hour, and minute values.")
        return
    if normalized_type == "monthly":
        if pattern.day_of_month is None or pattern.hour is None or pattern.minute is None:
            raise HTTPException(status_code=400, detail="Monthly schedules require day, hour, and minute values.")


def validate_snapshot_schedule_metadata(metadata: dict | None) -> None:
    payload = metadata if isinstance(metadata, dict) else {}
    keep_latest = payload.get("keep_latest", 0)
    try:
        keep_latest_value = int(keep_latest)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Snapshot retention keep_latest must be an integer.") from exc
    if keep_latest_value < 0:
        raise HTTPException(status_code=400, detail="Snapshot retention keep_latest cannot be negative.")


def require_dataset(*, dataset_name: str, state: AppState) -> dict:
    datasets = state.data.datasets or []
    dataset = next((item for item in datasets if item.get("name") == dataset_name), None)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_name!r} was not found in the latest snapshot.")
    return dataset


def require_snapshot(*, snapshot_name: str, state: AppState) -> dict:
    snapshots = state.data.datasets or []
    snapshot = next(
        (
            item
            for item in snapshots
            if str(item.get("name") or "") == snapshot_name and str(item.get("type") or "") == "snapshot"
        ),
        None,
    )
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_name!r} was not found in the latest snapshot.")
    return snapshot


def validate_dataset_property_changes(
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

    unsupported = sorted({str(change.property) for change in payload.changes if str(change.property) not in allowed})
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=(f"Unsupported dataset properties for type {dataset_type!r}: " f"{', '.join(unsupported)}"),
        )


def validate_dataset_creation(*, payload: DatasetCreateRequest, state: AppState) -> None:
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
    unsupported = sorted({str(property_item.name) for property_item in payload.properties if str(property_item.name) not in allowed})
    if unsupported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported create properties for type {payload.type!r}: {', '.join(unsupported)}",
        )


def validate_dataset_destroy(*, dataset: dict) -> None:
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


def validate_snapshot_parent(dataset: dict) -> None:
    dataset_type = str(dataset.get("type") or "")
    if dataset_type == "snapshot":
        raise HTTPException(status_code=400, detail="Cannot create a snapshot from another snapshot in this workflow.")


def validate_snapshot_destroy(snapshot: dict) -> None:
    properties = snapshot.get("properties")
    if not isinstance(properties, dict):
        return
    userrefs_entry = properties.get("userrefs")
    userrefs_value = userrefs_entry.get("value") if isinstance(userrefs_entry, dict) else None
    userrefs = coerce_int(userrefs_value, default=0)
    if userrefs > 0:
        raise HTTPException(
            status_code=400,
            detail="This snapshot currently has active user references and cannot be deleted in this workflow.",
        )


def validate_snapshot_rollback(*, snapshot: dict, state: AppState) -> None:
    snapshot_name = str(snapshot.get("name") or "")
    dataset_name = snapshot_name.split("@", 1)[0] if "@" in snapshot_name else ""
    if not dataset_name:
        raise HTTPException(status_code=400, detail="Snapshot rollback target is missing its parent dataset name.")
    dataset = next((item for item in (state.data.datasets or []) if str(item.get("name") or "") == dataset_name), None)
    if dataset is None:
        raise HTTPException(
            status_code=400,
            detail="The parent dataset is not available in the latest snapshot, so rollback cannot be offered here.",
        )
    dataset_type = str(dataset.get("type") or "")
    if dataset_type == "snapshot":
        raise HTTPException(status_code=400, detail="Snapshot rollback requires a live parent dataset.")


def validate_pool_removal(
    *,
    pool_name: str,
    payload: PoolRemoveRequest,
    state: AppState,
) -> dict:
    pool = require_pool(pool_name=pool_name, state=state)
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


def validate_pool_creation(*, payload: PoolCreateRequest, state: AppState) -> None:
    pools = state.data.pools or []
    if any(pool.get("name") == payload.name for pool in pools):
        raise HTTPException(status_code=400, detail=f"Pool {payload.name!r} already exists.")

    allowed_root_properties = DATASET_CREATE_ALLOWED_PROPERTIES["filesystem"]
    unsupported_root_properties = sorted(
        {str(property_item.name) for property_item in payload.root_dataset_properties if str(property_item.name) not in allowed_root_properties}
    )
    if unsupported_root_properties:
        raise HTTPException(
            status_code=400,
            detail=("Unsupported root dataset properties for pool creation: " f"{', '.join(unsupported_root_properties)}"),
        )

    disks = state.data.disks or []
    candidate_devices = {str(device.get("path")): device for device in disks if disk_is_available_for_creation(device)}

    selected_devices: set[str] = set()
    for vdev in payload.vdevs:
        for device_path in vdev.devices:
            if device_path in selected_devices:
                raise HTTPException(status_code=400, detail=f"Device {device_path!r} was selected more than once.")
            device = candidate_devices.get(device_path)
            if device is None:
                raise HTTPException(status_code=400, detail=f"Device {device_path!r} is not available for pool creation.")
            selected_devices.add(device_path)


def coerce_int(value, *, default: int = 0) -> int:
    if value in (None, "", "-"):
        return default
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def disk_is_available_for_creation(disk: dict) -> bool:
    if disk.get("poolName") and disk.get("poolName") != "-":
        return False
    filesystem = str(disk.get("filesystem") or "-").lower()
    if not is_reusable_filesystem(filesystem, disk.get("poolName")):
        return False
    for partition in disk.get("partitions", []):
        if partition.get("poolName") and partition.get("poolName") != "-":
            return False
        partition_filesystem = str(partition.get("filesystem") or "-").lower()
        if not is_reusable_filesystem(partition_filesystem, partition.get("poolName")):
            return False
    return True


def is_reusable_filesystem(filesystem: str | None, pool_name: str | None) -> bool:
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
