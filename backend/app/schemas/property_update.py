from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PropertyUpdateItem(BaseModel):
    property: str = Field(min_length=1)
    value: str
    old_value: Any = None


class PoolPropertyUpdateRequest(BaseModel):
    changes: list[PropertyUpdateItem] = Field(default_factory=list)


class PoolPropertyUpdateResult(BaseModel):
    property: str
    old_value: Any = None
    new_value: str
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None


class PoolPropertyUpdateResponse(BaseModel):
    pool: str
    results: list[PoolPropertyUpdateResult] = Field(default_factory=list)
    task_id: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
