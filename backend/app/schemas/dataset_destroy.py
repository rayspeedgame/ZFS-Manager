from __future__ import annotations

from pydantic import BaseModel


class DatasetDestroyResponse(BaseModel):
    dataset: str
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
