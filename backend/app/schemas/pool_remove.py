from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PoolRemoveRequest(BaseModel):
    command_target: str = Field(min_length=1)

    @field_validator("command_target")
    @classmethod
    def validate_command_target(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Removal target cannot be empty.")
        return normalized


class PoolRemoveResponse(BaseModel):
    pool: str
    command_target: str
    display_label: str
    target_type: str
    vdev_class: str
    layout: str
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
