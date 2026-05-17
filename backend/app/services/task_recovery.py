from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.task import TaskRecord
from app.schemas.zfs_state import AppState
from app.services.task_manager import TaskManager


TERMINAL_TASK_STATUSES = {"succeeded", "failed", "canceled", "unknown", "needs_attention"}


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
        "pool.topology",
        "dataset.create",
        "dataset.destroy",
        "dataset.properties",
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
        if task.kind == "pool.scrub.start":
            return _recover_pool_scrub_start(task, state)
        if task.kind == "pool.scrub.stop":
            return _recover_pool_scrub_stop(task, state)
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


def _pool_exists(state: AppState, pool_name: str) -> bool:
    return any(str(pool.get("name") or "") == pool_name for pool in (state.data.pools or []))


def _dataset_exists(state: AppState, dataset_name: str) -> bool:
    return any(str(dataset.get("name") or "") == dataset_name for dataset in (state.data.datasets or []))


def _recover_pool_scrub_start(task: TaskRecord, state: AppState) -> TaskRecoveryResult:
    pool = _get_pool(state, task.scope_name)
    scan = str((pool or {}).get("status", {}).get("scan") or "")
    scrub_info = _parse_scrub_scan(scan)
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
    scrub_info = _parse_scrub_scan(scan)
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


def _get_pool(state: AppState, pool_name: str) -> dict | None:
    return next((pool for pool in (state.data.pools or []) if str(pool.get("name") or "") == pool_name), None)


def _parse_scrub_scan(scan: str) -> dict[str, object]:
    normalized = str(scan or "").strip()
    lowered = normalized.lower()
    progress = _extract_scan_progress(normalized)
    eta = _extract_scan_eta(normalized)
    return {
        "active": "scrub in progress" in lowered,
        "completed": "scrub repaired" in lowered or "scrub completed" in lowered,
        "stopped": "scrub canceled" in lowered or "scrub cancelled" in lowered or "scrub stopped" in lowered,
        "kind": "scrub" if "scrub" in lowered else None,
        "progress": progress,
        "eta": eta,
    }


def _extract_scan_progress(scan: str) -> int:
    import re

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)%\s+done", scan, re.IGNORECASE)
    if not match:
        return 15 if "in progress" in scan.lower() else 100 if "repaired" in scan.lower() else 0
    return max(0, min(100, int(float(match.group(1)))))


def _extract_scan_eta(scan: str) -> str | None:
    import re

    match = re.search(r",\s*([^,]+?)\s+to go", scan, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()
