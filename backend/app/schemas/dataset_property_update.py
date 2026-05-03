from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatasetPropertyUpdateItem(BaseModel):
    property: str = Field(min_length=1)
    value: str
    old_value: Any = None


class DatasetPropertyUpdateRequest(BaseModel):
    changes: list[DatasetPropertyUpdateItem] = Field(default_factory=list)


class DatasetPropertyUpdateResult(BaseModel):
    property: str
    old_value: Any = None
    new_value: str
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None


class DatasetPropertyUpdateResponse(BaseModel):
    dataset: str
    results: list[DatasetPropertyUpdateResult] = Field(default_factory=list)
    refreshed: bool = False
    refresh_error: str | None = None
