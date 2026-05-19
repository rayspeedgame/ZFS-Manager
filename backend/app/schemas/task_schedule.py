from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskSchedulePattern(BaseModel):
    interval: int | None = Field(default=None, ge=1, le=60)
    weekday: int | None = Field(default=None, ge=0, le=6)
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    hour: int | None = Field(default=None, ge=0, le=23)
    minute: int | None = Field(default=None, ge=0, le=59)
    timezone: str = "local"


class TaskScheduleRecord(BaseModel):
    id: str
    title: str
    kind: str
    scope_type: str
    scope_name: str
    enabled: bool = True
    schedule_type: str = "weekly"
    pattern: TaskSchedulePattern
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
    last_result: str | None = None
    last_task_id: str | None = None
    next_run_at: datetime | None = None


class TaskScheduleCreateRequest(BaseModel):
    title: str
    kind: str
    scope_type: str
    scope_name: str
    enabled: bool = True
    schedule_type: str = "weekly"
    pattern: TaskSchedulePattern
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskScheduleUpdateRequest(BaseModel):
    title: str | None = None
    enabled: bool | None = None
    pattern: TaskSchedulePattern | None = None
    metadata: dict[str, Any] | None = None


class TaskScheduleListResponse(BaseModel):
    schedules: list[TaskScheduleRecord] = Field(default_factory=list)


class TaskScheduleDetailResponse(BaseModel):
    schedule: TaskScheduleRecord
