from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SnapshotListItem(BaseModel):
    id: str
    name: str
    full_name: str
    dataset: str
    pool: str
    created_at: datetime | None = None
    used: int | str | None = None
    referenced: int | str | None = None
    snapshot_type: str = "unknown"
    userrefs: int = 0
    strategy_name: str | None = None
    schedule_id: str | None = None
    schedule_level: str | None = None
    can_delete: bool = True
    can_rollback: bool = False
    delete_reason: str | None = None
    rollback_reason: str | None = None


class SnapshotListResponse(BaseModel):
    items: list[SnapshotListItem] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 25
    total_pages: int = 1


class SnapshotDetailResponse(BaseModel):
    snapshot: SnapshotListItem


class SnapshotFiltersResponse(BaseModel):
    pools: list[str] = Field(default_factory=list)
    datasets: list[str] = Field(default_factory=list)
    types: list[str] = Field(default_factory=list)


class DatasetSnapshotsResponse(BaseModel):
    snapshots: list[SnapshotListItem] = Field(default_factory=list)


class SnapshotCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    recursive: bool = False
    properties: dict[str, str] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Snapshot name cannot be empty.")
        if any(char.isspace() for char in normalized):
            raise ValueError("Snapshot name cannot contain whitespace.")
        if "@" in normalized or "/" in normalized:
            raise ValueError("Snapshot name cannot contain '@' or '/'.")
        return normalized


SnapshotRollbackMode = Literal["safe", "prune_newer", "force_dependents"]


class SnapshotRollbackRequest(BaseModel):
    mode: SnapshotRollbackMode = "safe"


class SnapshotCreateResponse(BaseModel):
    snapshot: str
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None


class SnapshotDestroyResponse(BaseModel):
    snapshot: str
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None


class SnapshotRollbackResponse(BaseModel):
    snapshot: str
    dataset: str
    rollback_mode: SnapshotRollbackMode = "safe"
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
