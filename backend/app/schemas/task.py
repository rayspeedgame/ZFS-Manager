from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskCommandLog(BaseModel):
    label: str
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None


class TaskRecord(BaseModel):
    id: str
    title: str
    kind: str
    scope_type: str
    scope_name: str
    status: str = "queued"
    progress: int = 0
    stage: str = "queued"
    message: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    command_logs: list[TaskCommandLog] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskListResponse(BaseModel):
    tasks: list[TaskRecord] = Field(default_factory=list)
    total: int = 0
    filtered_total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 1
    running_count: int = 0
    completed_count: int = 0
    failed_count: int = 0


class TaskDetailResponse(BaseModel):
    task: TaskRecord
