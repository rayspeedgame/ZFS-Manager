from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from app.schemas.task import TaskRecord
from app.schemas.zfs_state import AppState
from app.services.task_manager import TaskManager


TERMINAL_TASK_STATUSES = {"succeeded", "failed", "canceled", "unknown", "needs_attention"}
RAIDZ_EXPAND_OBSERVATION_TIMEOUT = timedelta(minutes=15)


@dataclass(slots=True)
class TaskRecoveryResult:
    status: str
    message: str
    progress: int
    stage: str
    metadata: dict = field(default_factory=dict)


class BaseTaskRecoveryHandler:
    def supports(self, task: TaskRecord) -> bool:
        raise NotImplementedError

    async def recover(self, task: TaskRecord, state: AppState) -> TaskRecoveryResult:
        raise NotImplementedError


class TaskRecoveryRegistry:
    def __init__(self, handlers: list[BaseTaskRecoveryHandler] | None = None) -> None:
        self._handlers = list(handlers or [])

    def register(self, handler: BaseTaskRecoveryHandler) -> None:
        self._handlers.append(handler)

    def resolve(self, task: TaskRecord) -> BaseTaskRecoveryHandler | None:
        return next((handler for handler in self._handlers if handler.supports(task)), None)


class TaskRecoveryService:
    def __init__(self, task_manager: TaskManager, registry: TaskRecoveryRegistry) -> None:
        self._task_manager = task_manager
        self._registry = registry

    async def recover_pending_tasks(self, state: AppState) -> None:
        pending_tasks = await self._task_manager.list_non_terminal_tasks()
        for task in pending_tasks:
            await self._task_manager.update_task(
                task.id,
                status="recovering",
                stage="recovering",
                message="Recovering task after backend restart...",
                progress=max(task.progress, 5),
            )

        for task in await self._task_manager.list_non_terminal_tasks():
            handler = self._registry.resolve(task)
            if handler is None:
                await self._task_manager.update_task(
                    task.id,
                    status="unknown",
                    stage="recovery-unavailable",
                    message="Task recovery is not available for this task type yet.",
                    progress=max(task.progress, 5),
                    metadata={"recovery_status": "unavailable"},
                )
                continue

            result = await handler.recover(task, state)
            await self._task_manager.update_task(
                task.id,
                status=result.status,
                stage=result.stage,
                message=result.message,
                progress=result.progress,
                metadata=result.metadata,
            )

    async def reconcile_active_tasks(self, state: AppState) -> None:
        for task in await self._task_manager.list_non_terminal_tasks():
            handler = self._registry.resolve(task)
            if handler is None:
                continue
            result = await handler.recover(task, state)
            await self._task_manager.update_task(
                task.id,
                status=result.status,
                stage=result.stage,
                message=result.message,
                progress=result.progress,
                metadata=result.metadata,
            )


class KnownWriteTaskRecoveryHandler(BaseTaskRecoveryHandler):
    """Recovery handler for the current write operations already shipped in the UI."""

    _SUPPORTED_KINDS = {
        "pool.create",
        "pool.destroy",
        "pool.remove",
        "pool.properties",
        "pool.scrub.start",
        "pool.scrub.stop",
        "pool.device.offline",
        "pool.device.online",
        "pool.clear",
        "pool.replace.start",
        "pool.raidz_expand.start",
        "pool.topology",
        "dataset.create",
        "dataset.destroy",
        "dataset.properties",
        "snapshot.create",
        "snapshot.delete",
        "snapshot.rollback",
    }

    def supports(self, task: TaskRecord) -> bool:
        return task.kind in self._SUPPORTED_KINDS

    async def recover(self, task: TaskRecord, state: AppState) -> TaskRecoveryResult:
        if task.kind == "pool.create":
            return _recover_pool_create(task, state)
        if task.kind == "pool.destroy":
            return _recover_pool_destroy(task, state)
        if task.kind == "dataset.create":
            return _recover_dataset_create(task, state)
        if task.kind == "dataset.destroy":
            return _recover_dataset_destroy(task, state)
        if task.kind == "snapshot.create":
            return _recover_snapshot_create(task, state)
        if task.kind == "snapshot.delete":
            return _recover_snapshot_delete(task, state)
        if task.kind == "pool.scrub.start":
            return _recover_pool_scrub_start(task, state)
        if task.kind == "pool.scrub.stop":
            return _recover_pool_scrub_stop(task, state)
        if task.kind == "pool.device.offline":
            return _recover_pool_device_offline(task, state)
        if task.kind == "pool.device.online":
            return _recover_pool_device_online(task, state)
        if task.kind == "pool.clear":
            return _recover_pool_clear(task, state)
        if task.kind == "pool.replace.start":
            return _recover_pool_replace_start(task, state)
        if task.kind == "pool.raidz_expand.start":
            return _recover_pool_raidz_expand_start(task, state)
        return TaskRecoveryResult(
            status="unknown",
            stage="recovery-needs-verification",
            progress=max(task.progress, 10),
            message=(
                "Backend restarted before this task completed, and the final effect "
                "cannot be safely inferred from the current snapshot alone."
            ),
            metadata={"recovery_status": "manual-verification-required"},
        )


def build_default_recovery_registry() -> TaskRecoveryRegistry:
    return TaskRecoveryRegistry(
        handlers=[
            KnownWriteTaskRecoveryHandler(),
        ]
    )


def _recover_pool_create(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if _pool_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: pool {task.scope_name} exists.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: pool {task.scope_name} was not found and completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _recover_pool_destroy(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if not _pool_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: pool {task.scope_name} is no longer present.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: pool {task.scope_name} still exists, so destroy completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _recover_dataset_create(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if _dataset_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: dataset {task.scope_name} exists.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: dataset {task.scope_name} was not found and completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _recover_dataset_destroy(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if not _dataset_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: dataset {task.scope_name} is no longer present.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: dataset {task.scope_name} still exists, so destroy completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _recover_snapshot_create(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if _snapshot_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: snapshot {task.scope_name} exists.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: snapshot {task.scope_name} was not found and completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _recover_snapshot_delete(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    if not _snapshot_exists(state, task.scope_name):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: snapshot {task.scope_name} is no longer present.",
            metadata={"recovery_status": "reconciled-from-state"},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: snapshot {task.scope_name} still exists, so delete completion could not be confirmed.",
        metadata={"recovery_status": "not-confirmed"},
    )


def _pool_exists(state: AppState, pool_name: str) -> bool:
    return any(str(pool.get("name") or "") == pool_name for pool in (state.data.pools or []))


def _dataset_exists(state: AppState, dataset_name: str) -> bool:
    return any(str(dataset.get("name") or "") == dataset_name for dataset in (state.data.datasets or []))


def _snapshot_exists(state: AppState, snapshot_name: str) -> bool:
    return any(
        str(dataset.get("name") or "") == snapshot_name and str(dataset.get("type") or "") == "snapshot"
        for dataset in (state.data.datasets or [])
    )


def _recover_pool_scrub_start(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    scan = str((pool or {}).get("status", {}).get("scan") or "")
    scrub_info = _parse_scan_status(scan)
    if scrub_info["active"]:
        return TaskRecoveryResult(
            status="running",
            stage="scrub-running",
            progress=int(scrub_info["progress"]),
            message=scan or f"Scrub is running for pool {task.scope_name}.",
            metadata={
                "recovery_status": "reconciled-from-state",
                "scan": scan,
                "scan_kind": scrub_info["kind"],
                "scan_eta": scrub_info["eta"],
            },
        )
    if scrub_info["completed"]:
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=scan or f"Recovered after restart: scrub completed for pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "scan": scan},
        )
    if scrub_info["stopped"]:
        return TaskRecoveryResult(
            status="canceled",
            stage="recovered-stopped",
            progress=max(task.progress, 10),
            message=scan or f"Recovered after restart: scrub was stopped for pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "scan": scan},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=(
            f"Recovered after restart: no active scrub was detected for pool {task.scope_name}, "
            "and completion could not be confirmed."
        ),
        metadata={"recovery_status": "not-confirmed", "scan": scan},
    )


def _recover_pool_scrub_stop(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    scan = str((pool or {}).get("status", {}).get("scan") or "")
    scrub_info = _parse_scan_status(scan)
    if not scrub_info["active"]:
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=scan or f"Recovered after restart: no active scrub is running for pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "scan": scan},
        )
    return TaskRecoveryResult(
        status="running",
        stage="scrub-stop-pending",
        progress=max(task.progress, 25),
        message=scan or f"Scrub is still running for pool {task.scope_name}.",
        metadata={"recovery_status": "still-running", "scan": scan},
    )


def _recover_pool_device_offline(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    command_target = str((task.metadata or {}).get("command_target") or "")
    member_state = _get_pool_member_state(state, pool_name=task.scope_name, command_target=command_target)
    if member_state == "OFFLINE":
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: device {command_target} is offline in pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "device_state": member_state},
        )
    if member_state:
        return TaskRecoveryResult(
            status="unknown",
            stage="recovery-needs-verification",
            progress=max(task.progress, 10),
            message=(
                f"Recovered after restart: device {command_target} is currently {member_state}, "
                "so offline completion could not be confirmed."
            ),
            metadata={"recovery_status": "not-confirmed", "device_state": member_state},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: device {command_target} was not found in pool {task.scope_name}.",
        metadata={"recovery_status": "target-missing"},
    )


def _recover_pool_device_online(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    command_target = str((task.metadata or {}).get("command_target") or "")
    member_state = _get_pool_member_state(state, pool_name=task.scope_name, command_target=command_target)
    if member_state and member_state != "OFFLINE":
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=f"Recovered after restart: device {command_target} is now {member_state} in pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "device_state": member_state},
        )
    if member_state == "OFFLINE":
        return TaskRecoveryResult(
            status="unknown",
            stage="recovery-needs-verification",
            progress=max(task.progress, 10),
            message=f"Recovered after restart: device {command_target} is still OFFLINE in pool {task.scope_name}.",
            metadata={"recovery_status": "not-confirmed", "device_state": member_state},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=f"Recovered after restart: device {command_target} was not found in pool {task.scope_name}.",
        metadata={"recovery_status": "target-missing"},
    )


def _recover_pool_clear(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    errors = str((pool or {}).get("status", {}).get("errors") or "").strip()
    if errors.lower().startswith("no known data errors"):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=errors or f"Recovered after restart: pool {task.scope_name} reports no known data errors.",
            metadata={"recovery_status": "reconciled-from-state", "pool_errors": errors},
        )
    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 10),
        message=(
            errors
            or f"Recovered after restart: pool {task.scope_name} error state could not safely confirm clear completion."
        ),
        metadata={"recovery_status": "not-confirmed", "pool_errors": errors},
    )


def _recover_pool_replace_start(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    scan = str((pool or {}).get("status", {}).get("scan") or "")
    scan_info = _parse_scan_status(scan)
    if scan_info["kind"] == "resilver" and scan_info["active"]:
        return TaskRecoveryResult(
            status="running",
            stage="resilver-running",
            progress=int(scan_info["progress"]),
            message=scan or f"Resilver is running for pool {task.scope_name}.",
            metadata={
                "recovery_status": "reconciled-from-state",
                "scan": scan,
                "scan_kind": scan_info["kind"],
                "scan_eta": scan_info["eta"],
            },
        )
    if scan_info["kind"] == "resilver" and scan_info["completed"]:
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=scan or f"Recovered after restart: resilver completed for pool {task.scope_name}.",
            metadata={"recovery_status": "reconciled-from-state", "scan": scan},
        )

    replacement_target = str((task.metadata or {}).get("replacement_target") or "")
    if replacement_target and _pool_has_member(state, pool_name=task.scope_name, target=replacement_target):
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=(
                f"Recovered after restart: replacement device {replacement_target} is present in pool {task.scope_name}."
            ),
            metadata={"recovery_status": "reconciled-from-state", "scan": scan},
        )

    return TaskRecoveryResult(
        status="unknown",
        stage="recovery-needs-verification",
        progress=max(task.progress, 20),
        message=(
            f"Recovered after restart: no active resilver was detected for pool {task.scope_name}, "
            "and replace completion could not be confirmed."
        ),
        metadata={"recovery_status": "not-confirmed", "scan": scan},
    )


def _recover_pool_raidz_expand_start(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    scan = str((pool or {}).get("status", {}).get("scan") or "")
    scan_info = _parse_scan_status(scan)
    expand = str((pool or {}).get("status", {}).get("expand") or "")
    expand_info = _parse_expand_status(expand)
    vdev_target = str((task.metadata or {}).get("vdev_target") or "")
    new_device_target = str((task.metadata or {}).get("new_device_target") or "")
    member_count_before = int((task.metadata or {}).get("member_count_before") or 0)
    member_count_after = _pool_vdev_member_count(state, pool_name=task.scope_name, vdev_target=vdev_target)
    new_member_present = _pool_vdev_has_member(
        state,
        pool_name=task.scope_name,
        vdev_target=vdev_target,
        target=new_device_target,
    )
    now = datetime.now(timezone.utc)
    observation_deadline = task.started_at or task.created_at

    if expand_info["active"]:
        return TaskRecoveryResult(
            status="running",
            stage="raidz-expand-running",
            progress=min(59, 20 + int(float(expand_info["progress"]) * 0.4)),
            message=expand or f"RAID-Z expansion is running for pool {task.scope_name}.",
            metadata={
                "recovery_status": "reconciled-from-state",
                "expand": expand,
                "expand_kind": expand_info["kind"],
                "expand_eta": expand_info["eta"],
                "scan": scan,
                "scan_kind": scan_info["kind"],
                "scan_eta": scan_info["eta"],
                "vdev_target": vdev_target,
            },
        )

    # OpenZFS exposes RAID-Z expansion in two observable phases:
    # 1. the explicit `expand:` phase for the reshape itself
    # 2. the automatic follow-up `scrub` after reshape completion
    # Keep both phases visible in one task so operators do not see the task
    # jump straight from "running" to "done" while scrub is still active.
    if expand_info["completed"] and scan_info["kind"] == "scrub" and scan_info["active"]:
        return TaskRecoveryResult(
            status="running",
            stage="raidz-expand-scrubbing",
            progress=min(99, 60 + int(float(scan_info["progress"]) * 0.4)),
            message=scan or f"Automatic scrub is running after RAID-Z expansion for pool {task.scope_name}.",
            metadata={
                "recovery_status": "reconciled-from-state",
                "expand": expand,
                "expand_kind": expand_info["kind"],
                "scan": scan,
                "scan_kind": scan_info["kind"],
                "scan_eta": scan_info["eta"],
                "vdev_target": vdev_target,
            },
        )

    # Final success requires both status phases plus a topology confirmation.
    # The extra member-presence check prevents us from trusting status text
    # alone when the topology snapshot has not yet reflected the new device.
    if expand_info["completed"] and scan_info["kind"] == "scrub" and scan_info["completed"] and new_member_present and member_count_after > member_count_before:
        return TaskRecoveryResult(
            status="succeeded",
            stage="recovered-completed",
            progress=100,
            message=(
                expand
                or scan
                or f"Recovered after restart: RAID-Z vdev {vdev_target} now includes {new_device_target} in pool {task.scope_name}."
            ),
            metadata={
                "recovery_status": "reconciled-from-state",
                "expand": expand,
                "scan": scan,
                "vdev_target": vdev_target,
            },
        )

    # Expansion signals can lag behind the initial attach command, but the
    # task should not remain in "watching" forever if no observable state is
    # ever exposed by the host.
    if now - observation_deadline >= RAIDZ_EXPAND_OBSERVATION_TIMEOUT:
        return TaskRecoveryResult(
            status="needs_attention",
            stage="raidz-expand-observation-timeout",
            progress=max(task.progress, 20),
            message=(
                f"RAID-Z expansion for pool {task.scope_name} did not expose observable progress or completion "
                "signals before the observation timeout. Please verify the pool state manually."
            ),
            metadata={
                "recovery_status": "observation-timeout",
                "expand": expand,
                "scan": scan,
                "vdev_target": vdev_target,
            },
        )

    return TaskRecoveryResult(
        # RAID-Z expansion state can lag behind the initial attach command.
        # Keep the task non-terminal so later refresh cycles can still observe
        # the scan text or the expanded vdev membership.
        status="running",
        stage="raidz-expand-awaiting-observation",
        progress=max(task.progress, 20),
        message=(
            f"No active RAID-Z expansion was confirmed yet for pool {task.scope_name}. "
            "The task will keep watching later refresh cycles for expansion progress."
        ),
        metadata={"recovery_status": "awaiting-observation", "expand": expand, "scan": scan, "vdev_target": vdev_target},
    )


def _get_pool(state: AppState, pool_name: str) -> dict | None:
    return next((pool for pool in (state.data.pools or []) if str(pool.get("name") or "") == pool_name), None)


def _parse_scan_status(scan: str) -> dict[str, object]:
    normalized = str(scan or "").strip()
    lowered = normalized.lower()
    progress = _extract_scan_progress(normalized)
    eta = _extract_scan_eta(normalized)
    kind = (
        "scrub"
        if "scrub" in lowered
        else (
            "resilver"
            if "resilver" in lowered or "resilvered" in lowered
            else "expansion" if "expand" in lowered or "expansion" in lowered else None
        )
    )
    return {
        "active": "in progress" in lowered,
        "completed": (
            "scrub repaired" in lowered
            or "scrub completed" in lowered
            or ("resilvered" in lowered and "in progress" not in lowered)
        ),
        "stopped": (
            "scrub canceled" in lowered
            or "scrub cancelled" in lowered
            or "scrub stopped" in lowered
            or "resilver canceled" in lowered
            or "resilver cancelled" in lowered
            or "resilver stopped" in lowered
        ),
        "kind": kind,
        "progress": progress,
        "eta": eta,
    }


def _parse_expand_status(expand: str) -> dict[str, object]:
    normalized = str(expand or "").strip()
    lowered = normalized.lower()
    progress = _extract_scan_progress(normalized)
    eta = _extract_scan_eta(normalized)
    return {
        "active": "in progress" in lowered,
        "completed": "expanded" in lowered and "in progress" not in lowered,
        "stopped": "canceled" in lowered or "cancelled" in lowered or "stopped" in lowered,
        "kind": "expansion" if normalized else None,
        "progress": progress,
        "eta": eta,
    }


def _extract_scan_progress(scan: str) -> int:
    import re

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)%\s+done", scan, re.IGNORECASE)
    if not match:
        lowered = scan.lower()
        return 15 if "in progress" in lowered else 100 if ("repaired" in lowered or "resilvered" in lowered) else 0
    return max(0, min(100, int(float(match.group(1)))))


def _extract_scan_eta(scan: str) -> str | None:
    import re

    match = re.search(r",\s*([^,]+?)\s+to go", scan, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _get_pool_member_state(state: AppState, *, pool_name: str, command_target: str) -> str | None:
    pool = _get_pool(state, pool_name)
    if not pool:
        return None
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            for member in item.get("members") or []:
                candidates = {
                    str(member.get("commandTarget") or "").strip(),
                    str(member.get("rawCommandTarget") or "").strip(),
                    str(member.get("path") or "").strip(),
                    str(member.get("kernelPath") or "").strip(),
                    str(member.get("byIdPath") or "").strip(),
                    str(member.get("displayLabel") or "").strip(),
                }
                for alias in member.get("aliases") or []:
                    alias_text = str(alias or "").strip()
                    if alias_text:
                        candidates.add(alias_text)
                candidates.discard("")
                if command_target in candidates:
                    normalized = str(member.get("state") or "").strip().upper()
                    return normalized or None
    for node in _walk_pool_status_nodes((pool.get("status") or {}).get("config") or []):
        if str(node.get("name") or "") == command_target:
            normalized = str(node.get("state") or "").strip().upper()
            return normalized or None
    return None


def _pool_has_member(state: AppState, *, pool_name: str, target: str) -> bool:
    pool = _get_pool(state, pool_name)
    if not pool:
        return False
    normalized = str(target or "").strip()
    if not normalized:
        return False
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            for member in item.get("members") or []:
                candidates = {
                    str(member.get("commandTarget") or "").strip(),
                    str(member.get("rawCommandTarget") or "").strip(),
                    str(member.get("path") or "").strip(),
                    str(member.get("kernelPath") or "").strip(),
                    str(member.get("byIdPath") or "").strip(),
                    str(member.get("displayLabel") or "").strip(),
                }
                for alias in member.get("aliases") or []:
                    alias_text = str(alias or "").strip()
                    if alias_text:
                        candidates.add(alias_text)
                candidates.discard("")
                if normalized in candidates:
                    return True
    return False


def _pool_vdev_member_count(state: AppState, *, pool_name: str, vdev_target: str) -> int:
    pool = _get_pool(state, pool_name)
    if not pool:
        return 0
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            if _pool_item_matches_target(item, vdev_target):
                return len(item.get("members") or [])
    return 0


def _pool_vdev_has_member(state: AppState, *, pool_name: str, vdev_target: str, target: str) -> bool:
    pool = _get_pool(state, pool_name)
    if not pool:
        return False
    normalized = str(target or "").strip()
    if not normalized:
        return False
    for group in pool.get("topologySummary") or []:
        for item in group.get("items") or []:
            if not _pool_item_matches_target(item, vdev_target):
                continue
            for member in item.get("members") or []:
                candidates = {
                    str(member.get("commandTarget") or "").strip(),
                    str(member.get("rawCommandTarget") or "").strip(),
                    str(member.get("path") or "").strip(),
                    str(member.get("kernelPath") or "").strip(),
                    str(member.get("byIdPath") or "").strip(),
                    str(member.get("displayLabel") or "").strip(),
                    str(member.get("diskId") or "").strip(),
                }
                for alias in member.get("aliases") or []:
                    alias_text = str(alias or "").strip()
                    if alias_text:
                        candidates.add(alias_text)
                candidates.discard("")
                if normalized in candidates:
                    return True
    return False


def _pool_item_matches_target(item: dict, target: str) -> bool:
    normalized = str(target or "").strip()
    if not normalized:
        return False
    candidates = {
        str(item.get("name") or "").strip(),
        str(item.get("commandTarget") or "").strip(),
        str(item.get("rawCommandTarget") or "").strip(),
        str(item.get("displayLabel") or "").strip(),
    }
    candidates.discard("")
    return normalized in candidates


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
