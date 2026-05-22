from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PoolDeviceActionRequest(BaseModel):
    command_target: str = Field(min_length=1)

    @field_validator("command_target")
    @classmethod
    def validate_command_target(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Pool device target cannot be empty.")
        return normalized


class PoolMaintenanceActionResponse(BaseModel):
    pool: str
    action: str
    success: bool
    message: str
    command_target: str | None = None
    display_label: str | None = None
    device_state: str | None = None
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
