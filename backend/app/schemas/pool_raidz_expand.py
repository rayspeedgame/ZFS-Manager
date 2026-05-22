from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PoolRaidzExpandRequest(BaseModel):
    vdev_target: str = Field(min_length=1)
    new_device_target: str = Field(min_length=1)

    @field_validator("vdev_target", "new_device_target")
    @classmethod
    def validate_target(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("RAID-Z expansion targets cannot be empty.")
        return normalized


class PoolRaidzExpandResponse(BaseModel):
    pool: str
    success: bool
    message: str
    vdev_target: str
    new_device_target: str
    vdev_label: str | None = None
    new_device_label: str | None = None
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
