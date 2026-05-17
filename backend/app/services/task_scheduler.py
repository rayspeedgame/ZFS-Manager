from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import uuid4

from app.core.state import state_store
from app.schemas.task import TaskCommandLog
from app.schemas.task_schedule import (
    TaskScheduleCreateRequest,
    TaskSchedulePattern,
    TaskScheduleRecord,
    TaskScheduleUpdateRequest,
)
from app.services.pool_scrubber import PoolScrubber
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
        refresh_state: Callable[..., object],
        tick_seconds: int = 30,
    ) -> None:
        self._store = store
        self._task_manager = task_manager
        self._task_recovery_service = task_recovery_service
        self._pool_scrubber = pool_scrubber
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
        _validate_schedule_payload(payload.kind, payload.scope_type, payload.scope_name, payload.schedule_type, payload.pattern)
        now = datetime.now(timezone.utc)
        schedule = TaskScheduleRecord(
            id=uuid4().hex,
            title=payload.title.strip(),
            kind=payload.kind,
            scope_type=payload.scope_type,
            scope_name=payload.scope_name,
            enabled=bool(payload.enabled),
            schedule_type=payload.schedule_type,
            pattern=payload.pattern.model_copy(deep=True),
            metadata=dict(payload.metadata or {}),
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
                )
                schedule.pattern = payload.pattern.model_copy(deep=True)
            if payload.metadata is not None:
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
        if schedule.kind != "pool.scrub.schedule":
            await self._record_schedule_outcome(
                schedule_id=schedule.id,
                triggered_at=triggered_at,
                last_result="unsupported_schedule_kind",
            )
            return

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
) -> None:
    if kind != "pool.scrub.schedule":
        raise ValueError(f"Unsupported schedule kind: {kind!r}")
    if scope_type != "pool":
        raise ValueError("Scheduled scrub currently only supports pool scope.")
    if not scope_name.strip():
        raise ValueError("A pool name is required for scheduled scrub.")
    if schedule_type != "weekly":
        raise ValueError(f"Unsupported schedule type: {schedule_type!r}")
    if not isinstance(pattern, TaskSchedulePattern):
        raise ValueError("A valid weekly schedule pattern is required.")


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
    if schedule_type != "weekly":
        return None

    local_reference = reference.astimezone()
    days_ahead = (pattern.weekday - local_reference.weekday()) % 7
    candidate = (local_reference + timedelta(days=days_ahead)).replace(
        hour=pattern.hour,
        minute=pattern.minute,
        second=0,
        microsecond=0,
    )
    if candidate <= local_reference:
        candidate += timedelta(days=7)
    return candidate.astimezone(timezone.utc)


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
