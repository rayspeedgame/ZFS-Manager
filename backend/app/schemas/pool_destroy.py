from __future__ import annotations

from pydantic import BaseModel


class PoolDestroyResponse(BaseModel):
    pool: str
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
