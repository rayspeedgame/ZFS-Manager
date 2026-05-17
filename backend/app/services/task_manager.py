from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.task import TaskCommandLog, TaskRecord
from app.services.task_store import SQLiteTaskStore


class TaskManager:
    """In-memory registry for operator-visible background and write tasks."""

    def __init__(self, *, max_tasks: int = 200, store: SQLiteTaskStore | None = None) -> None:
        self._lock = asyncio.Lock()
        self._tasks: dict[str, TaskRecord] = {}
        self._order: deque[str] = deque()
        self._max_tasks = max(20, max_tasks)
        self._store = store

    async def startup(self) -> None:
        if self._store is None:
            return
        await self._store.initialize()
        persisted_tasks = await self._store.load_recent_tasks(limit=self._max_tasks)
        async with self._lock:
            self._tasks = {task.id: task for task in persisted_tasks}
            self._order = deque(task.id for task in persisted_tasks)

    async def list_tasks(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> tuple[list[TaskRecord], int, int, int, int, int, int, int, int]:
        async with self._lock:
            normalized_page = max(1, int(page))
            normalized_page_size = max(1, min(100, int(page_size)))
            normalized_filter = str(status_filter or "").strip().lower()
            all_task_ids = list(self._order)
            if normalized_filter:
                filtered_task_ids = [
                    task_id
                    for task_id in all_task_ids
                    if str(self._tasks[task_id].status).lower() == normalized_filter
                ]
            else:
                filtered_task_ids = all_task_ids
            total = len(all_task_ids)
            filtered_total = len(filtered_task_ids)
            total_pages = max(1, (filtered_total + normalized_page_size - 1) // normalized_page_size)
            start_index = (min(normalized_page, total_pages) - 1) * normalized_page_size
            end_index = start_index + normalized_page_size
            page_task_ids = filtered_task_ids[start_index:end_index]
            tasks = [self._tasks[task_id].model_copy(deep=True) for task_id in page_task_ids]
            running_count = sum(1 for task in self._tasks.values() if task.status == "running")
            completed_count = sum(1 for task in self._tasks.values() if task.status == "succeeded")
            failed_count = sum(1 for task in self._tasks.values() if task.status == "failed")
            return (
                tasks,
                total,
                filtered_total,
                min(normalized_page, total_pages),
                normalized_page_size,
                total_pages,
                running_count,
                completed_count,
                failed_count,
            )

    async def get_task(self, task_id: str) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.model_copy(deep=True) if task else None

    async def list_non_terminal_tasks(self) -> list[TaskRecord]:
        async with self._lock:
            return [
                self._tasks[task_id].model_copy(deep=True)
                for task_id in self._order
                if self._tasks[task_id].status not in {"succeeded", "failed", "canceled", "unknown", "needs_attention"}
            ]

    async def create_task(
        self,
        *,
        title: str,
        kind: str,
        scope_type: str,
        scope_name: str,
        message: str = "",
        metadata: dict | None = None,
    ) -> TaskRecord:
        now = datetime.now(timezone.utc)
        task = TaskRecord(
            id=uuid4().hex,
            title=title,
            kind=kind,
            scope_type=scope_type,
            scope_name=scope_name,
            status="queued",
            progress=0,
            stage="queued",
            message=message,
            created_at=now,
            metadata=dict(metadata or {}),
        )
        async with self._lock:
            self._tasks[task.id] = task
            self._order.appendleft(task.id)
            self._trim_locked()
            snapshot = task.model_copy(deep=True)
        await self._persist_task(snapshot)
        return snapshot

    async def mark_running(
        self,
        task_id: str,
        *,
        message: str,
        progress: int = 10,
        stage: str = "running",
    ) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.status = "running"
            task.progress = _normalize_progress(progress)
            task.stage = stage
            task.message = message
            task.started_at = task.started_at or datetime.now(timezone.utc)
            snapshot = task.model_copy(deep=True)
        await self._persist_task(snapshot)
        return snapshot

    async def mark_finished(
        self,
        task_id: str,
        *,
        success: bool,
        message: str,
        progress: int = 100,
        stage: str = "completed",
        command_logs: list[TaskCommandLog] | None = None,
        metadata: dict | None = None,
    ) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            task.status = "succeeded" if success else "failed"
            task.progress = _normalize_progress(progress if success else min(progress, 100))
            task.stage = stage
            task.message = message
            task.started_at = task.started_at or datetime.now(timezone.utc)
            task.finished_at = datetime.now(timezone.utc)
            if command_logs is not None:
                task.command_logs = list(command_logs)
            if metadata:
                task.metadata.update(metadata)
            snapshot = task.model_copy(deep=True)
        await self._persist_task(snapshot)
        return snapshot

    async def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        message: str | None = None,
        progress: int | None = None,
        stage: str | None = None,
        metadata: dict | None = None,
        command_logs: list[TaskCommandLog] | None = None,
    ) -> TaskRecord | None:
        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            if status is not None:
                task.status = status
                if status in {"succeeded", "failed", "canceled", "unknown", "needs_attention"}:
                    task.finished_at = task.finished_at or datetime.now(timezone.utc)
                elif status in {"running", "recovering"}:
                    task.started_at = task.started_at or datetime.now(timezone.utc)
            if message is not None:
                task.message = message
            if progress is not None:
                task.progress = _normalize_progress(progress)
            if stage is not None:
                task.stage = stage
            if metadata:
                task.metadata.update(metadata)
            if command_logs is not None:
                task.command_logs = list(command_logs)
            snapshot = task.model_copy(deep=True)
        await self._persist_task(snapshot)
        return snapshot

    def _trim_locked(self) -> None:
        while len(self._order) > self._max_tasks:
            tail_id = self._order.pop()
            self._tasks.pop(tail_id, None)

    async def _persist_task(self, task: TaskRecord) -> None:
        if self._store is None:
            return
        await self._store.save_task(task)


def _normalize_progress(progress: int) -> int:
    return max(0, min(100, int(progress)))
