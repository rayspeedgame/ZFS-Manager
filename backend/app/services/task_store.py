from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.task import TaskCommandLog, TaskRecord
from app.schemas.task_schedule import TaskSchedulePattern, TaskScheduleRecord


class SQLiteTaskStore:
    """SQLite-backed persistence for operator-visible tasks."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)

    async def initialize(self) -> None:
        await asyncio.to_thread(self._initialize_sync)

    async def load_recent_tasks(self, *, limit: int) -> list[TaskRecord]:
        return await asyncio.to_thread(self._load_recent_tasks_sync, limit)

    async def save_task(self, task: TaskRecord) -> None:
        await asyncio.to_thread(self._save_task_sync, task.model_copy(deep=True))

    async def load_schedules(self) -> list[TaskScheduleRecord]:
        return await asyncio.to_thread(self._load_schedules_sync)

    async def save_schedule(self, schedule: TaskScheduleRecord) -> None:
        await asyncio.to_thread(self._save_schedule_sync, schedule.model_copy(deep=True))

    async def delete_schedule(self, schedule_id: str) -> None:
        await asyncio.to_thread(self._delete_schedule_sync, str(schedule_id))

    def _initialize_sync(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scope_type TEXT NOT NULL,
                    scope_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    command_logs_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_schedules (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scope_type TEXT NOT NULL,
                    scope_name TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    schedule_type TEXT NOT NULL,
                    pattern_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_run_at TEXT,
                    last_result TEXT,
                    last_task_id TEXT,
                    next_run_at TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_task_schedules_next_run_at ON task_schedules(next_run_at)"
            )
            conn.commit()

    def _load_recent_tasks_sync(self, limit: int) -> list[TaskRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    title,
                    kind,
                    scope_type,
                    scope_name,
                    status,
                    progress,
                    stage,
                    message,
                    created_at,
                    started_at,
                    finished_at,
                    command_logs_json,
                    metadata_json
                FROM tasks
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def _save_task_sync(self, task: TaskRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id,
                    title,
                    kind,
                    scope_type,
                    scope_name,
                    status,
                    progress,
                    stage,
                    message,
                    created_at,
                    started_at,
                    finished_at,
                    command_logs_json,
                    metadata_json,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    kind = excluded.kind,
                    scope_type = excluded.scope_type,
                    scope_name = excluded.scope_name,
                    status = excluded.status,
                    progress = excluded.progress,
                    stage = excluded.stage,
                    message = excluded.message,
                    created_at = excluded.created_at,
                    started_at = excluded.started_at,
                    finished_at = excluded.finished_at,
                    command_logs_json = excluded.command_logs_json,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
                """,
                (
                    task.id,
                    task.title,
                    task.kind,
                    task.scope_type,
                    task.scope_name,
                    task.status,
                    int(task.progress),
                    task.stage,
                    task.message,
                    _serialize_datetime(task.created_at),
                    _serialize_datetime(task.started_at),
                    _serialize_datetime(task.finished_at),
                    json.dumps([item.model_dump(mode="json") for item in task.command_logs]),
                    json.dumps(task.metadata),
                    _serialize_datetime(datetime.utcnow()),
                ),
            )
            conn.commit()

    def _load_schedules_sync(self) -> list[TaskScheduleRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    title,
                    kind,
                    scope_type,
                    scope_name,
                    enabled,
                    schedule_type,
                    pattern_json,
                    metadata_json,
                    created_at,
                    updated_at,
                    last_run_at,
                    last_result,
                    last_task_id,
                    next_run_at
                FROM task_schedules
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._row_to_schedule(row) for row in rows]

    def _save_schedule_sync(self, schedule: TaskScheduleRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO task_schedules (
                    id,
                    title,
                    kind,
                    scope_type,
                    scope_name,
                    enabled,
                    schedule_type,
                    pattern_json,
                    metadata_json,
                    created_at,
                    updated_at,
                    last_run_at,
                    last_result,
                    last_task_id,
                    next_run_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    kind = excluded.kind,
                    scope_type = excluded.scope_type,
                    scope_name = excluded.scope_name,
                    enabled = excluded.enabled,
                    schedule_type = excluded.schedule_type,
                    pattern_json = excluded.pattern_json,
                    metadata_json = excluded.metadata_json,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    last_run_at = excluded.last_run_at,
                    last_result = excluded.last_result,
                    last_task_id = excluded.last_task_id,
                    next_run_at = excluded.next_run_at
                """,
                (
                    schedule.id,
                    schedule.title,
                    schedule.kind,
                    schedule.scope_type,
                    schedule.scope_name,
                    1 if schedule.enabled else 0,
                    schedule.schedule_type,
                    json.dumps(schedule.pattern.model_dump(mode="json")),
                    json.dumps(schedule.metadata),
                    _serialize_datetime(schedule.created_at),
                    _serialize_datetime(schedule.updated_at),
                    _serialize_datetime(schedule.last_run_at),
                    schedule.last_result,
                    schedule.last_task_id,
                    _serialize_datetime(schedule.next_run_at),
                ),
            )
            conn.commit()

    def _delete_schedule_sync(self, schedule_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM task_schedules WHERE id = ?", (schedule_id,))
            conn.commit()

    def _row_to_task(self, row: sqlite3.Row) -> TaskRecord:
        command_logs_data = json.loads(row["command_logs_json"] or "[]")
        metadata = json.loads(row["metadata_json"] or "{}")
        return TaskRecord(
            id=str(row["id"]),
            title=str(row["title"]),
            kind=str(row["kind"]),
            scope_type=str(row["scope_type"]),
            scope_name=str(row["scope_name"]),
            status=str(row["status"]),
            progress=int(row["progress"]),
            stage=str(row["stage"]),
            message=str(row["message"]),
            created_at=_parse_datetime(row["created_at"]),
            started_at=_parse_datetime(row["started_at"]),
            finished_at=_parse_datetime(row["finished_at"]),
            command_logs=[TaskCommandLog.model_validate(item) for item in command_logs_data],
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    def _row_to_schedule(self, row: sqlite3.Row) -> TaskScheduleRecord:
        pattern_data = json.loads(row["pattern_json"] or "{}")
        metadata = json.loads(row["metadata_json"] or "{}")
        return TaskScheduleRecord(
            id=str(row["id"]),
            title=str(row["title"]),
            kind=str(row["kind"]),
            scope_type=str(row["scope_type"]),
            scope_name=str(row["scope_name"]),
            enabled=bool(row["enabled"]),
            schedule_type=str(row["schedule_type"]),
            pattern=TaskSchedulePattern.model_validate(pattern_data),
            metadata=metadata if isinstance(metadata, dict) else {},
            created_at=_parse_datetime(row["created_at"]) or datetime.now(timezone.utc),
            updated_at=_parse_datetime(row["updated_at"]) or datetime.now(timezone.utc),
            last_run_at=_parse_datetime(row["last_run_at"]),
            last_result=str(row["last_result"]) if row["last_result"] is not None else None,
            last_task_id=str(row["last_task_id"]) if row["last_task_id"] is not None else None,
            next_run_at=_parse_datetime(row["next_run_at"]),
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)
