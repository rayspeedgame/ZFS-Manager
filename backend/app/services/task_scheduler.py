from __future__ import annotations

import asyncio
import calendar
from datetime import datetime, timedelta, timezone
from re import sub
from typing import Callable
from uuid import uuid4

from app.core.state import state_store
from app.schemas.snapshot import SnapshotCreateRequest
from app.schemas.task import TaskCommandLog
from app.schemas.task_schedule import (
    TaskScheduleCreateRequest,
    TaskSchedulePattern,
    TaskScheduleRecord,
    TaskScheduleUpdateRequest,
)
from app.services.pool_scrubber import PoolScrubber
from app.services.snapshot_creator import SnapshotCreator
from app.services.snapshot_destroyer import SnapshotDestroyer
from app.services.snapshot_metadata import build_scheduled_snapshot_properties
from app.services.snapshot_retention import build_scheduled_snapshot_name, plan_snapshot_retention
from app.services.task_manager import TaskManager
from app.services.task_recovery import TaskRecoveryService
from app.services.task_store import SQLiteTaskStore


class TaskSchedulerService:
    """Background scheduler for recurring operator-defined tasks."""

    def __init__(
        self,
        *,
        store: SQLiteTaskStore,
        task_manager: TaskManager,
        task_recovery_service: TaskRecoveryService,
        pool_scrubber: PoolScrubber,
        snapshot_creator: SnapshotCreator,
        snapshot_destroyer: SnapshotDestroyer,
        refresh_state: Callable[..., object],
        tick_seconds: int = 30,
    ) -> None:
        self._store = store
        self._task_manager = task_manager
        self._task_recovery_service = task_recovery_service
        self._pool_scrubber = pool_scrubber
        self._snapshot_creator = snapshot_creator
        self._snapshot_destroyer = snapshot_destroyer
        self._refresh_state = refresh_state
        self._tick_seconds = max(5, int(tick_seconds))
        self._lock = asyncio.Lock()
        self._schedules: dict[str, TaskScheduleRecord] = {}
        self._runner: asyncio.Task | None = None
        self._stop_event: asyncio.Event | None = None

    async def startup(self) -> None:
        await self._store.initialize()
        schedules = await self._store.load_schedules()
        async with self._lock:
            self._schedules = {schedule.id: schedule for schedule in schedules}
            for schedule in self._schedules.values():
                if not schedule.enabled:
                    schedule.next_run_at = None
                elif schedule.next_run_at is None:
                    schedule.next_run_at = _compute_next_run_at(schedule)
        self._stop_event = asyncio.Event()
        self._runner = asyncio.create_task(self._run_loop(), name="task-scheduler")

    async def shutdown(self) -> None:
        stop_event = self._stop_event
        runner = self._runner
        self._runner = None
        self._stop_event = None
        if stop_event is not None:
            stop_event.set()
        if runner is not None:
            runner.cancel()
            try:
                await runner
            except asyncio.CancelledError:
                pass

    async def list_schedules(self) -> list[TaskScheduleRecord]:
        async with self._lock:
            schedules = [schedule.model_copy(deep=True) for schedule in self._schedules.values()]
        return sorted(
            schedules,
            key=lambda item: (
                item.next_run_at or datetime.max.replace(tzinfo=timezone.utc),
                item.created_at,
            ),
        )

    async def get_schedule(self, schedule_id: str) -> TaskScheduleRecord | None:
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            return schedule.model_copy(deep=True) if schedule else None

    async def create_schedule(self, payload: TaskScheduleCreateRequest) -> TaskScheduleRecord:
        _validate_schedule_payload(
            payload.kind,
            payload.scope_type,
            payload.scope_name,
            payload.schedule_type,
            payload.pattern,
            payload.metadata,
        )
        now = datetime.now(timezone.utc)
        metadata = dict(payload.metadata or {})
        if payload.kind == "snapshot.schedule":
            metadata = _build_snapshot_schedule_metadata(
                scope_name=payload.scope_name,
                schedule_type=payload.schedule_type,
                metadata=metadata,
                existing_schedules=self._schedules.values(),
            )
        schedule = TaskScheduleRecord(
            id=uuid4().hex,
            title=payload.title.strip(),
            kind=payload.kind,
            scope_type=payload.scope_type,
            scope_name=payload.scope_name,
            enabled=bool(payload.enabled),
            schedule_type=payload.schedule_type,
            pattern=payload.pattern.model_copy(deep=True),
            metadata=metadata,
            created_at=now,
            updated_at=now,
            next_run_at=_compute_next_run_at_from_parts(bool(payload.enabled), payload.schedule_type, payload.pattern, now),
        )
        async with self._lock:
            self._schedules[schedule.id] = schedule
            snapshot = schedule.model_copy(deep=True)
        await self._store.save_schedule(snapshot)
        return snapshot

    async def update_schedule(self, schedule_id: str, payload: TaskScheduleUpdateRequest) -> TaskScheduleRecord | None:
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            if schedule is None:
                return None
            if payload.title is not None:
                schedule.title = payload.title.strip()
            if payload.enabled is not None:
                schedule.enabled = bool(payload.enabled)
            if payload.pattern is not None:
                _validate_schedule_payload(
                    schedule.kind,
                    schedule.scope_type,
                    schedule.scope_name,
                    schedule.schedule_type,
                    payload.pattern,
                    payload.metadata if payload.metadata is not None else schedule.metadata,
                )
                schedule.pattern = payload.pattern.model_copy(deep=True)
            if payload.metadata is not None:
                if schedule.kind == "snapshot.schedule":
                    _validate_snapshot_schedule_metadata(payload.metadata)
                schedule.metadata = dict(payload.metadata)
            schedule.updated_at = datetime.now(timezone.utc)
            schedule.next_run_at = _compute_next_run_at(schedule)
            snapshot = schedule.model_copy(deep=True)
        await self._store.save_schedule(snapshot)
        return snapshot

    async def delete_schedule(self, schedule_id: str) -> bool:
        async with self._lock:
            existed = schedule_id in self._schedules
            if existed:
                self._schedules.pop(schedule_id, None)
        if existed:
            await self._store.delete_schedule(schedule_id)
        return existed

    async def _run_loop(self) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            return
        while not stop_event.is_set():
            try:
                await self._run_due_schedules_once()
            except Exception:
                # Keep the scheduler alive even when one pass fails.
                pass
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self._tick_seconds)
            except asyncio.TimeoutError:
                continue

    async def _run_due_schedules_once(self) -> None:
        now = datetime.now(timezone.utc)
        async with self._lock:
            due_schedules = [
                schedule.model_copy(deep=True)
                for schedule in self._schedules.values()
                if schedule.enabled and schedule.next_run_at and schedule.next_run_at <= now
            ]

        for schedule in due_schedules:
            await self._execute_schedule(schedule, now)

    async def _execute_schedule(self, schedule: TaskScheduleRecord, triggered_at: datetime) -> None:
        if schedule.kind == "pool.scrub.schedule":
            await self._execute_pool_scrub_schedule(schedule, triggered_at)
            return

        if schedule.kind == "snapshot.schedule":
            await self._execute_snapshot_schedule(schedule, triggered_at)
            return

        await self._record_schedule_outcome(
            schedule_id=schedule.id,
            triggered_at=triggered_at,
            last_result="unsupported_schedule_kind",
        )

    async def _execute_pool_scrub_schedule(self, schedule: TaskScheduleRecord, triggered_at: datetime) -> None:
        state = await state_store.get_state()
        pools = state.data.pools or []
        pool = next((item for item in pools if item.get("name") == schedule.scope_name), None)
        if pool is None:
            task = await self._task_manager.create_task(
                title=schedule.title,
                kind="pool.scrub.start",
                scope_type="pool",
                scope_name=schedule.scope_name,
                message="Scheduled scrub could not start because the pool was not found.",
                metadata={"schedule_id": schedule.id, "trigger": "scheduler"},
            )
            await self._task_manager.update_task(
                task.id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Scheduled scrub skipped because pool {schedule.scope_name!r} was not found.",
            )
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="pool_not_found",
                last_task_id=task.id,
            )
            return

        if _pool_has_active_scrub(pool):
            task = await self._task_manager.create_task(
                title=schedule.title,
                kind="pool.scrub.start",
                scope_type="pool",
                scope_name=schedule.scope_name,
                message="Scheduled scrub was skipped because another scrub is already active.",
                metadata={"schedule_id": schedule.id, "trigger": "scheduler"},
            )
            await self._task_manager.update_task(
                task.id,
                status="canceled",
                progress=100,
                stage="skipped",
                message=f"Scheduled scrub skipped because pool {schedule.scope_name} already has an active scrub.",
            )
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="skipped_active_scrub",
                last_task_id=task.id,
            )
            return

        task = await self._task_manager.create_task(
            title=schedule.title,
            kind="pool.scrub.start",
            scope_type="pool",
            scope_name=schedule.scope_name,
            message="Queued scheduled scrub start.",
            metadata={"schedule_id": schedule.id, "trigger": "scheduler"},
        )
        await self._task_manager.mark_running(
            task.id,
            message=f"Starting scheduled scrub for pool {schedule.scope_name}...",
            progress=15,
            stage="scrub-starting",
        )

        result = await self._pool_scrubber.start_scrub(schedule.scope_name)

        refreshed = False
        refresh_error: str | None = None
        refreshed_state = state
        try:
            refreshed_state = await self._refresh_state(force_all=True)
            refreshed = True
        except Exception as exc:
            refresh_error = str(exc)

        command_log = _task_log_from_single_result(label=schedule.scope_name, result=result)
        if not result.success:
            await self._task_manager.mark_finished(
                task.id,
                success=False,
                progress=100,
                stage="failed",
                message=_build_single_result_task_message(
                    success=False,
                    success_text=f"Scheduled scrub start submitted for pool {schedule.scope_name}.",
                    failure_text=result.message,
                    refresh_error=refresh_error,
                ),
                command_logs=[command_log],
                metadata={"schedule_id": schedule.id, "refreshed": refreshed, "refresh_error": refresh_error},
            )
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="failed",
                last_task_id=task.id,
            )
            return

        await self._task_recovery_service.reconcile_active_tasks(refreshed_state)
        await self._task_manager.update_task(
            task.id,
            message=(result.message if not refresh_error else f"{result.message} State refresh warning: {refresh_error}"),
            metadata={
                "schedule_id": schedule.id,
                "refreshed": refreshed,
                "refresh_error": refresh_error,
                "command": result.command,
                "exit_status": result.exit_status,
            },
            command_logs=[command_log],
        )
        await self._record_schedule_outcome(
            schedule_id=schedule.id,
            triggered_at=triggered_at,
            last_result="submitted",
            last_task_id=task.id,
        )

    async def _execute_snapshot_schedule(self, schedule: TaskScheduleRecord, triggered_at: datetime) -> None:
        state = await state_store.get_state()
        datasets = state.data.datasets or []
        dataset = next((item for item in datasets if item.get("name") == schedule.scope_name), None)
        if dataset is None or str(dataset.get("type") or "") == "snapshot":
            task = await self._task_manager.create_task(
                title=schedule.title,
                kind="snapshot.schedule.run",
                scope_type="dataset",
                scope_name=schedule.scope_name,
                message="Scheduled snapshot could not start because the dataset was not found.",
                metadata={"schedule_id": schedule.id, "trigger": "scheduler"},
            )
            await self._task_manager.update_task(
                task.id,
                status="failed",
                progress=100,
                stage="failed",
                message=f"Scheduled snapshot skipped because dataset {schedule.scope_name!r} was not found.",
            )
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="dataset_not_found",
                last_task_id=task.id,
            )
            return

        # The visible snapshot name stays short and low-risk. All strategy
        # ownership and retention identity live in ZFS user properties instead.
        snapshot_prefix = _snapshot_schedule_prefix(schedule)
        strategy_name = _snapshot_schedule_strategy_name(schedule)
        keep_latest = _snapshot_schedule_keep_latest(schedule)
        recursive = _snapshot_schedule_recursive(schedule)
        snapshot_name = build_scheduled_snapshot_name(triggered_at=triggered_at)

        task = await self._task_manager.create_task(
            title=schedule.title,
            kind="snapshot.schedule.run",
            scope_type="dataset",
            scope_name=schedule.scope_name,
            message="Queued scheduled snapshot creation.",
            metadata={
                "schedule_id": schedule.id,
                "trigger": "scheduler",
                "strategy_name": strategy_name,
                "snapshot_prefix": snapshot_prefix,
                "snapshot_name": snapshot_name,
                "schedule_level": schedule.schedule_type,
                "recursive": recursive,
                "keep_latest": keep_latest,
            },
        )
        await self._task_manager.mark_running(
            task.id,
            message=f"Creating scheduled snapshot {schedule.scope_name}@{snapshot_name}...",
            progress=15,
            stage="snapshot-creating",
        )

        create_result = await self._snapshot_creator.create_snapshot(
            schedule.scope_name,
            SnapshotCreateRequest(
                name=snapshot_name,
                recursive=recursive,
                properties=build_scheduled_snapshot_properties(
                    schedule_id=schedule.id,
                    strategy_name=strategy_name,
                    schedule_level=schedule.schedule_type,
                    keep_latest=keep_latest,
                    recursive=recursive,
                ),
            ),
        )
        command_logs = [_task_log_from_single_result(label=f"{schedule.scope_name}@{snapshot_name}", result=create_result)]

        refreshed = False
        refresh_error: str | None = None
        refreshed_state = state
        try:
            refreshed_state = await self._refresh_state(force_all=True)
            refreshed = True
        except Exception as exc:
            refresh_error = str(exc)

        if not create_result.success:
            await self._task_manager.mark_finished(
                task.id,
                success=False,
                progress=100,
                stage="failed",
                message=_build_single_result_task_message(
                    success=False,
                    success_text=f"Scheduled snapshot {schedule.scope_name}@{snapshot_name} created.",
                    failure_text=create_result.message,
                    refresh_error=refresh_error,
                ),
                command_logs=command_logs,
                metadata={
                    "schedule_id": schedule.id,
                    "refreshed": refreshed,
                    "refresh_error": refresh_error,
                    "snapshot_name": snapshot_name,
                },
            )
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="failed",
                last_task_id=task.id,
            )
            return

        # Retention is keyed by the schedule id written into each snapshot's
        # user properties, so one scheduled rule only cleans up its own output.
        retention_plan = plan_snapshot_retention(
            refreshed_state,
            schedule_id=schedule.id,
            keep_latest=keep_latest,
        )
        cleanup_failures: list[str] = []
        if retention_plan.delete:
            await self._task_manager.update_task(
                task.id,
                message=f"Scheduled snapshot created. Cleaning up {len(retention_plan.delete)} older snapshots...",
                progress=70,
                stage="snapshot-cleanup",
            )
        for snapshot_full_name in retention_plan.delete:
            # Even for recursive schedules we delete one concrete snapshot at a
            # time here. The retention planner has already expanded matching
            # snapshots per dataset, which avoids broad recursive destroy calls.
            destroy_result = await self._snapshot_destroyer.destroy_snapshot(snapshot_full_name, recursive=False)
            command_logs.append(_task_log_from_single_result(label=snapshot_full_name, result=destroy_result))
            if not destroy_result.success:
                cleanup_failures.append(f"{snapshot_full_name}: {destroy_result.message}")

        if retention_plan.delete:
            try:
                refreshed_state = await self._refresh_state(force_all=True)
                refreshed = True
            except Exception as exc:
                refresh_error = str(exc)

        success = not cleanup_failures
        last_result = "submitted" if success else "cleanup_failed"
        message = (
            f"Scheduled snapshot {schedule.scope_name}@{snapshot_name} created."
            if success
            else (
                f"Scheduled snapshot {schedule.scope_name}@{snapshot_name} created, "
                f"but retention cleanup failed for {len(cleanup_failures)} snapshot(s)."
            )
        )
        if keep_latest > 0 and not cleanup_failures:
            message = (
                f"Scheduled snapshot {schedule.scope_name}@{snapshot_name} created. "
                f"Retention kept the latest {keep_latest} matching snapshots."
            )
        if cleanup_failures:
            message = f"{message} {'; '.join(cleanup_failures)}"
        if refresh_error:
            message = f"{message} State refresh warning: {refresh_error}"

        await self._task_manager.mark_finished(
            task.id,
            success=success,
            progress=100,
            stage="completed" if success else "cleanup-failed",
            message=message,
            command_logs=command_logs,
            metadata={
                "schedule_id": schedule.id,
                "refreshed": refreshed,
                "refresh_error": refresh_error,
                "snapshot_name": snapshot_name,
                "strategy_name": strategy_name,
                "snapshot_prefix": snapshot_prefix,
                "keep_latest": keep_latest,
                "deleted_snapshots": retention_plan.delete,
            },
        )
        await self._record_schedule_outcome(
            schedule_id=schedule.id,
            triggered_at=triggered_at,
            last_result=last_result,
            last_task_id=task.id,
        )
        return

    async def _record_schedule_outcome(
        self,
        *,
        schedule_id: str,
        triggered_at: datetime,
        last_result: str,
        last_task_id: str | None = None,
    ) -> None:
        async with self._lock:
            schedule = self._schedules.get(schedule_id)
            if schedule is None:
                return
            schedule.last_run_at = triggered_at
            schedule.last_result = last_result
            schedule.last_task_id = last_task_id
            schedule.updated_at = datetime.now(timezone.utc)
            schedule.next_run_at = _compute_next_run_at(schedule, triggered_at + timedelta(seconds=1))
            snapshot = schedule.model_copy(deep=True)
        await self._store.save_schedule(snapshot)


def _validate_schedule_payload(
    kind: str,
    scope_type: str,
    scope_name: str,
    schedule_type: str,
    pattern: TaskSchedulePattern,
    metadata: dict | None = None,
) -> None:
    if kind == "pool.scrub.schedule":
        if scope_type != "pool":
            raise ValueError("Scheduled scrub currently only supports pool scope.")
        if not scope_name.strip():
            raise ValueError("A pool name is required for scheduled scrub.")
        if schedule_type != "weekly":
            raise ValueError("Scheduled scrub currently only supports weekly recurrence.")
    elif kind == "snapshot.schedule":
        if scope_type != "dataset":
            raise ValueError("Scheduled snapshots currently only support dataset scope.")
        if not scope_name.strip():
            raise ValueError("A dataset name is required for scheduled snapshots.")
        _validate_snapshot_schedule_metadata(metadata or {})
    else:
        raise ValueError(f"Unsupported schedule kind: {kind!r}")
    if schedule_type not in {"minutely", "hourly", "daily", "weekly", "monthly"}:
        raise ValueError(f"Unsupported schedule type: {schedule_type!r}")
    if not isinstance(pattern, TaskSchedulePattern):
        raise ValueError("A valid schedule pattern is required.")
    _validate_schedule_pattern(schedule_type, pattern)


def _compute_next_run_at(
    schedule: TaskScheduleRecord,
    reference: datetime | None = None,
) -> datetime | None:
    return _compute_next_run_at_from_parts(
        schedule.enabled,
        schedule.schedule_type,
        schedule.pattern,
        reference or datetime.now(timezone.utc),
    )


def _compute_next_run_at_from_parts(
    enabled: bool,
    schedule_type: str,
    pattern: TaskSchedulePattern,
    reference: datetime,
) -> datetime | None:
    if not enabled:
        return None

    local_reference = reference.astimezone()
    normalized_type = str(schedule_type or "").lower()

    if normalized_type == "minutely":
        # Align the next run to the next interval bucket inside the current
        # hour, then roll into the next hour when needed.
        interval = max(1, int(pattern.interval or 1))
        minute_bucket = ((local_reference.minute // interval) + 1) * interval
        candidate = local_reference.replace(second=0, microsecond=0)
        if minute_bucket >= 60:
            candidate = candidate.replace(minute=0) + timedelta(hours=1)
        else:
            candidate = candidate.replace(minute=minute_bucket)
        return candidate.astimezone(timezone.utc)

    if normalized_type == "hourly":
        # Hourly schedules use "every N hours at minute M" semantics.
        interval = max(1, min(24, int(pattern.interval or 1)))
        target_minute = int(pattern.minute or 0)
        current_hour = local_reference.hour
        next_hour = ((current_hour // interval) + 1) * interval
        candidate = local_reference.replace(second=0, microsecond=0, minute=target_minute)
        if next_hour >= 24:
            candidate = (candidate.replace(hour=0) + timedelta(days=1))
        else:
            candidate = candidate.replace(hour=next_hour)
        if candidate <= local_reference:
            candidate += timedelta(hours=interval)
        return candidate.astimezone(timezone.utc)

    if normalized_type == "daily":
        candidate = local_reference.replace(
            hour=int(pattern.hour or 0),
            minute=int(pattern.minute or 0),
            second=0,
            microsecond=0,
        )
        if candidate <= local_reference:
            candidate += timedelta(days=1)
        return candidate.astimezone(timezone.utc)

    if normalized_type == "weekly":
        days_ahead = (int(pattern.weekday or 0) - local_reference.weekday()) % 7
        candidate = (local_reference + timedelta(days=days_ahead)).replace(
            hour=int(pattern.hour or 0),
            minute=int(pattern.minute or 0),
            second=0,
            microsecond=0,
        )
        if candidate <= local_reference:
            candidate += timedelta(days=7)
        return candidate.astimezone(timezone.utc)

    if normalized_type == "monthly":
        # Clamp oversized day-of-month values (for example 31 in February) to
        # the last valid day of the target month.
        target_day = int(pattern.day_of_month or 1)
        candidate = _replace_with_clamped_day(
            local_reference,
            day=target_day,
            hour=int(pattern.hour or 0),
            minute=int(pattern.minute or 0),
        )
        if candidate <= local_reference:
            next_month_reference = _add_months(local_reference, 1)
            candidate = _replace_with_clamped_day(
                next_month_reference,
                day=target_day,
                hour=int(pattern.hour or 0),
                minute=int(pattern.minute or 0),
            )
        return candidate.astimezone(timezone.utc)

    return None


def _pool_has_active_scrub(pool: dict) -> bool:
    scan_status = pool.get("scanStatus") or {}
    if scan_status.get("kind") == "scrub" and scan_status.get("active"):
        return True
    scan = str((pool.get("status") or {}).get("scan") or "").lower()
    return "scrub in progress" in scan


def _build_single_result_task_message(
    *,
    success: bool,
    success_text: str,
    failure_text: str,
    refresh_error: str | None,
) -> str:
    message = success_text if success else failure_text
    if refresh_error:
        return f"{message} State refresh warning: {refresh_error}"
    return message


def _task_log_from_single_result(*, label: str, result) -> TaskCommandLog:
    return TaskCommandLog(
        label=label,
        success=bool(getattr(result, "success", False)),
        message=str(getattr(result, "message", "")),
        command=getattr(result, "command", None),
        exit_status=getattr(result, "exit_status", None),
        stdout=getattr(result, "stdout", None),
        stderr=getattr(result, "stderr", None),
    )


def _snapshot_schedule_prefix(schedule: TaskScheduleRecord) -> str:
    return f"scheduled-{_snapshot_schedule_strategy_name(schedule)}"


def _snapshot_schedule_strategy_name(schedule: TaskScheduleRecord) -> str:
    metadata = schedule.metadata if isinstance(schedule.metadata, dict) else {}
    strategy_name = str(metadata.get("strategy_name") or "").strip()
    if strategy_name:
        return strategy_name
    legacy_prefix = str(metadata.get("snapshot_prefix") or "").strip()
    if legacy_prefix:
        return _sanitize_schedule_token(legacy_prefix)
    dataset_token = _dataset_scope_token(schedule.scope_name)
    return f"{dataset_token}-{schedule.schedule_type}-001"


def _snapshot_schedule_keep_latest(schedule: TaskScheduleRecord) -> int:
    metadata = schedule.metadata if isinstance(schedule.metadata, dict) else {}
    try:
        return max(0, int(metadata.get("keep_latest") or 0))
    except (TypeError, ValueError):
        return 0


def _snapshot_schedule_recursive(schedule: TaskScheduleRecord) -> bool:
    metadata = schedule.metadata if isinstance(schedule.metadata, dict) else {}
    return bool(metadata.get("recursive"))


def _validate_snapshot_schedule_metadata(metadata: dict) -> None:
    keep_latest = metadata.get("keep_latest", 0)
    try:
        keep_latest_value = int(keep_latest)
    except (TypeError, ValueError) as exc:
        raise ValueError("Snapshot retention keep_latest must be an integer.") from exc
    if keep_latest_value < 0:
        raise ValueError("Snapshot retention keep_latest cannot be negative.")


def _validate_schedule_pattern(schedule_type: str, pattern: TaskSchedulePattern) -> None:
    normalized_type = str(schedule_type or "").lower()
    if normalized_type == "minutely":
        if pattern.interval is None:
            raise ValueError("Minutely schedules require an interval.")
        return
    if normalized_type == "hourly":
        if pattern.interval is None:
            raise ValueError("Hourly schedules require an interval.")
        if pattern.minute is None:
            raise ValueError("Hourly schedules require a minute value.")
        return
    if normalized_type == "daily":
        if pattern.hour is None or pattern.minute is None:
            raise ValueError("Daily schedules require hour and minute values.")
        return
    if normalized_type == "weekly":
        if pattern.weekday is None or pattern.hour is None or pattern.minute is None:
            raise ValueError("Weekly schedules require weekday, hour, and minute values.")
        return
    if normalized_type == "monthly":
        if pattern.day_of_month is None or pattern.hour is None or pattern.minute is None:
            raise ValueError("Monthly schedules require day, hour, and minute values.")
        return
    raise ValueError(f"Unsupported schedule type: {schedule_type!r}")


def _build_snapshot_schedule_metadata(
    *,
    scope_name: str,
    schedule_type: str,
    metadata: dict,
    existing_schedules,
) -> dict:
    next_metadata = dict(metadata or {})
    strategy_name = str(next_metadata.get("strategy_name") or "").strip()
    if not strategy_name:
        strategy_name = _generate_snapshot_strategy_name(
            scope_name=scope_name,
            schedule_type=schedule_type,
            existing_schedules=existing_schedules,
        )
    next_metadata["strategy_name"] = strategy_name
    next_metadata.pop("snapshot_prefix", None)
    return next_metadata


def _generate_snapshot_strategy_name(*, scope_name: str, schedule_type: str, existing_schedules) -> str:
    dataset_token = _dataset_scope_token(scope_name)
    normalized_schedule_type = _sanitize_schedule_token(schedule_type or "weekly")
    prefix = f"{dataset_token}-{normalized_schedule_type}-"
    max_index = 0
    for schedule in existing_schedules:
        if getattr(schedule, "kind", "") != "snapshot.schedule":
            continue
        if str(getattr(schedule, "scope_name", "")) != str(scope_name):
            continue
        candidate = _snapshot_schedule_strategy_name(schedule)
        if not candidate.startswith(prefix):
            continue
        suffix = candidate[len(prefix):]
        try:
            max_index = max(max_index, int(suffix))
        except (TypeError, ValueError):
            continue
    return f"{prefix}{max_index + 1:03d}"


def _dataset_scope_token(scope_name: str) -> str:
    normalized = str(scope_name or "").strip()
    normalized = normalized.replace("/", "__")
    return _sanitize_schedule_token(normalized or "dataset")


def _sanitize_schedule_token(value: str) -> str:
    normalized = sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip())
    normalized = normalized.strip("._-")
    return normalized or "item"


def _replace_with_clamped_day(reference: datetime, *, day: int, hour: int, minute: int) -> datetime:
    last_day = calendar.monthrange(reference.year, reference.month)[1]
    safe_day = max(1, min(int(day), last_day))
    return reference.replace(day=safe_day, hour=hour, minute=minute, second=0, microsecond=0)


def _add_months(reference: datetime, months: int) -> datetime:
    total_month = (reference.month - 1) + int(months)
    year = reference.year + (total_month // 12)
    month = (total_month % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    return reference.replace(year=year, month=month, day=min(reference.day, last_day))
