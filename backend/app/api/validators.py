from __future__ import annotations

from fastapi import HTTPException

from app import runtime
from app.api.constants import DATASET_CREATE_ALLOWED_PROPERTIES, DATASET_EDITABLE_PROPERTIES
from app.core.state import state_store
from app.schemas.dataset_create import DatasetCreateRequest
from app.schemas.dataset_property_update import DatasetPropertyUpdateRequest
from app.schemas.pool_create import PoolCreateRequest
from app.schemas.pool_maintenance import PoolDeviceActionRequest
from app.schemas.pool_raidz_expand import PoolRaidzExpandRequest
from app.schemas.pool_replace import PoolReplaceRequest
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
        key: device
        for device in (pool.get("availableTopologyDevices") or [])
        for key in {
            str(device.get("commandPath") or "").strip(),
            str(device.get("path") or "").strip(),
            str(device.get("diskKey") or "").strip(),
        }
        if key
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
    targets = pool.get("removalTargets") or []
    # Removal targets now expose both a display-friendly alias and a preferred
    # execution target. Match against either form so UI refresh timing cannot
    # strand a valid user selection.
    target = next((item for item in targets if _pool_removal_matches_target(item, payload.command_target)), None)
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"Target {payload.command_target!r} is not removable in the latest snapshot.",
        )
    return target


def validate_pool_device_action(
    *,
    pool_name: str,
    payload: PoolDeviceActionRequest,
    state: AppState,
    expected_action: str,
) -> dict:
    pool = require_pool(pool_name=pool_name, state=state)
    targets = _collect_pool_device_targets(pool)
    target = next((item for item in targets if _pool_device_matches_target(item, payload.command_target)), None)
    if target is None:
        target = _find_pool_status_device_target(pool, payload.command_target)
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"Device target {payload.command_target!r} is not available in the latest topology snapshot.",
        )

    if expected_action == "offline" and not target.get("canOffline"):
        raise HTTPException(
            status_code=400,
            detail=str(target.get("offlineReason") or f"Device {payload.command_target!r} cannot be offlined right now."),
        )
    if expected_action == "online" and not target.get("canOnline"):
        raise HTTPException(
            status_code=400,
            detail=str(target.get("onlineReason") or f"Device {payload.command_target!r} cannot be onlined right now."),
        )
    return target


def validate_pool_device_replace(
    *,
    pool_name: str,
    payload: PoolReplaceRequest,
    state: AppState,
) -> tuple[dict, dict]:
    pool = require_pool(pool_name=pool_name, state=state)
    targets = _collect_pool_device_targets(pool)
    target = next((item for item in targets if _pool_device_matches_target(item, payload.command_target)), None)
    if target is None:
        target = _find_pool_status_device_target(pool, payload.command_target)
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"Device target {payload.command_target!r} is not available in the latest topology snapshot.",
        )
    if not target.get("canReplace"):
        raise HTTPException(
            status_code=400,
            detail=str(target.get("replaceReason") or f"Device {payload.command_target!r} cannot be replaced right now."),
        )

    replacement = next(
        (
            item
            for item in (target.get("replaceCandidates") or [])
            if _pool_replace_candidate_matches_target(item, payload.replacement_target)
        ),
        None,
    )
    if replacement is None:
        raise HTTPException(
            status_code=400,
            detail=f"Replacement target {payload.replacement_target!r} is not available for pool replace.",
    )
    return target, replacement


def validate_pool_raidz_expand(
    *,
    pool_name: str,
    payload: PoolRaidzExpandRequest,
    state: AppState,
) -> tuple[dict, dict]:
    pool = require_pool(pool_name=pool_name, state=state)
    target = next(
        (
            item
            for item in _collect_pool_vdev_targets(pool)
            if _pool_vdev_matches_target(item, payload.vdev_target)
        ),
        None,
    )
    if target is None:
        raise HTTPException(
            status_code=400,
            detail=f"RAID-Z target {payload.vdev_target!r} is not available in the latest topology snapshot.",
        )
    if not target.get("canRaidzExpand"):
        raise HTTPException(
            status_code=400,
            detail=str(target.get("raidzExpandReason") or f"RAID-Z target {payload.vdev_target!r} cannot be expanded right now."),
        )

    replacement = next(
        (
            item
            for item in (target.get("raidzExpandCandidates") or [])
            if _pool_replace_candidate_matches_target(item, payload.new_device_target)
        ),
        None,
    )
    if replacement is None:
        raise HTTPException(
            status_code=400,
            detail=f"Expansion device {payload.new_device_target!r} is not available for RAID-Z expansion.",
        )
    minimum_size = coerce_int(target.get("smallestMemberSize"), default=0)
    replacement_size = coerce_int(replacement.get("size"), default=0)
    if minimum_size > 0 and replacement_size > 0 and replacement_size < minimum_size:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Expansion device {payload.new_device_target!r} is smaller than the current "
                f"smallest RAID-Z member and cannot be used for expansion."
            ),
        )
    return target, replacement


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
    candidate_devices = {
        key: device
        for device in disks
        if disk_is_available_for_creation(device)
        for key in {
            str(device.get("commandPath") or "").strip(),
            str(device.get("path") or "").strip(),
            str(device.get("diskKey") or "").strip(),
        }
        if key
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


def _collect_pool_device_targets(pool: dict) -> list[dict]:
    targets: list[dict] = []
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            for member in item.get("members") or []:
                if member.get("commandTarget"):
                    targets.append(member)
    return targets


def _collect_pool_vdev_targets(pool: dict) -> list[dict]:
    targets: list[dict] = []
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            if str(item.get("nodeKind") or "") == "vdev":
                targets.append(item)
    return targets


def _pool_device_matches_target(member: dict, target: str) -> bool:
    normalized = str(target or "").strip()
    if not normalized:
        return False
    candidates = {
        str(member.get("commandTarget") or "").strip(),
        str(member.get("rawCommandTarget") or "").strip(),
        str(member.get("path") or "").strip(),
        str(member.get("kernelPath") or "").strip(),
        str(member.get("byIdPath") or "").strip(),
        str(member.get("name") or "").strip(),
        str(member.get("diskId") or "").strip(),
        str(member.get("displayLabel") or "").strip(),
    }
    for alias in member.get("aliases") or []:
        alias_text = str(alias or "").strip()
        if alias_text:
            candidates.add(alias_text)
    candidates.discard("")
    return normalized in candidates


def _pool_vdev_matches_target(item: dict, target: str) -> bool:
    normalized = str(target or "").strip()
    if not normalized:
        return False
    candidates = {
        str(item.get("commandTarget") or "").strip(),
        str(item.get("rawCommandTarget") or "").strip(),
        str(item.get("displayLabel") or "").strip(),
        str(item.get("name") or "").strip(),
    }
    candidates.discard("")
    return normalized in candidates


def _pool_removal_matches_target(target_info: dict, target: str) -> bool:
    normalized = str(target or "").strip()
    if not normalized:
        return False
    candidates = {
        str(target_info.get("commandTarget") or "").strip(),
        str(target_info.get("rawCommandTarget") or "").strip(),
        str(target_info.get("displayLabel") or "").strip(),
        str(target_info.get("name") or "").strip(),
    }
    for member in target_info.get("members") or []:
        for key in ("commandTarget", "rawCommandTarget", "displayLabel", "path", "kernelPath", "byIdPath", "diskId"):
            value = str(member.get(key) or "").strip()
            if value:
                candidates.add(value)
        for alias in member.get("aliases") or []:
            alias_text = str(alias or "").strip()
            if alias_text:
                candidates.add(alias_text)
    candidates.discard("")
    return normalized in candidates


def _pool_replace_candidate_matches_target(candidate: dict, target: str) -> bool:
    normalized = str(target or "").strip()
    if not normalized:
        return False
    candidates = {
        str(candidate.get("commandPath") or "").strip(),
        str(candidate.get("path") or "").strip(),
        str(candidate.get("kernelPath") or "").strip(),
        str(candidate.get("byIdPath") or "").strip(),
        str(candidate.get("diskKey") or "").strip(),
        str(candidate.get("diskId") or "").strip(),
        str(candidate.get("displayName") or "").strip(),
        str(candidate.get("name") or "").strip(),
    }
    candidates.discard("")
    return normalized in candidates


def _find_pool_status_device_target(pool: dict, target: str) -> dict | None:
    normalized = str(target or "").strip()
    if not normalized:
        return None

    for node in _walk_pool_status_nodes((pool.get("status") or {}).get("config") or []):
        if not _pool_status_node_is_device(node):
            continue
        candidates = {
            str(node.get("name") or "").strip(),
            str(node.get("display_name") or "").strip(),
            str(node.get("displayName") or "").strip(),
        }
        candidates.discard("")
        if normalized not in candidates:
            continue
        state = str(node.get("state") or "").strip().upper() or None
        command_target = str(node.get("name") or normalized)
        display_label = str(node.get("display_name") or node.get("displayName") or command_target)
        return {
            "name": command_target,
            "path": display_label,
            "displayLabel": display_label,
            "commandTarget": command_target,
            "rawCommandTarget": command_target,
            "state": state,
            "canOffline": state in {"ONLINE", "DEGRADED"},
            "canOnline": state == "OFFLINE",
            "canReplace": False,
            "replaceReason": "Replace requires a fully enriched topology member from the latest snapshot.",
            "offlineReason": None if state in {"ONLINE", "DEGRADED"} else (
                "This device is already offline." if state == "OFFLINE" else f"Offline is not offered for device state {state or 'UNKNOWN'}."
            ),
            "onlineReason": None if state == "OFFLINE" else (
                "Online is only offered when the device is OFFLINE."
            ),
        }
    return None


def _walk_pool_status_nodes(nodes: list[dict]) -> list[dict]:
    collected: list[dict] = []
    pending = list(nodes or [])
    while pending:
        node = pending.pop(0)
        if not isinstance(node, dict):
            continue
        collected.append(node)
        pending.extend(node.get("children") or [])
    return collected


def _pool_status_node_is_device(node: dict) -> bool:
    node_kind = str(node.get("node_kind") or "").strip().lower()
    if node_kind:
        return node_kind == "device"
    children = node.get("children") or []
    return not children
