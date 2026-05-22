from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PoolReplaceRequest(BaseModel):
    command_target: str = Field(min_length=1)
    replacement_target: str = Field(min_length=1)

    @field_validator("command_target", "replacement_target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Pool replace targets cannot be empty.")
        return normalized


class PoolReplaceResponse(BaseModel):
    pool: str
    success: bool
    message: str
    command_target: str
    replacement_target: str
    display_label: str | None = None
    replacement_label: str | None = None
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
