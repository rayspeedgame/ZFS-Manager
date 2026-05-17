from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


PoolCreateCategory = Literal["data", "log", "cache", "special", "dedup", "spare"]
PoolCreateLayout = Literal["stripe", "mirror", "raidz", "raidz2", "raidz3"]


class PoolCreatePropertyItem(BaseModel):
    name: str = Field(min_length=1)
    value: str


class PoolCreateVdevItem(BaseModel):
    category: PoolCreateCategory
    layout: PoolCreateLayout = "stripe"
    devices: list[str] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_layout(self) -> "PoolCreateVdevItem":
        if self.category in {"cache", "spare"} and self.layout != "stripe":
            raise ValueError(f"{self.category} only supports stripe layout.")
        if self.category in {"log", "special", "dedup"} and self.layout not in {"stripe", "mirror"}:
            raise ValueError(f"{self.category} only supports stripe or mirror layout.")
        if self.layout == "mirror" and len(self.devices) < 2:
            raise ValueError("mirror layout requires at least 2 devices.")
        if self.layout == "raidz" and len(self.devices) < 2:
            raise ValueError("raidz layout requires at least 2 devices.")
        if self.layout == "raidz2" and len(self.devices) < 3:
            raise ValueError("raidz2 layout requires at least 3 devices.")
        if self.layout == "raidz3" and len(self.devices) < 4:
            raise ValueError("raidz3 layout requires at least 4 devices.")
        return self


class PoolCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    force: bool = False
    properties: list[PoolCreatePropertyItem] = Field(default_factory=list)
    root_dataset_properties: list[PoolCreatePropertyItem] = Field(default_factory=list)
    vdevs: list[PoolCreateVdevItem] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Pool name cannot be empty.")
        if any(char.isspace() for char in normalized):
            raise ValueError("Pool name cannot contain whitespace.")
        return normalized

    @model_validator(mode="after")
    def validate_vdevs(self) -> "PoolCreateRequest":
        if not self.vdevs:
            raise ValueError("At least one vdev is required.")
        if not any(vdev.category == "data" for vdev in self.vdevs):
            raise ValueError("At least one data vdev is required.")
        return self


class PoolCreateResponse(BaseModel):
    pool: str
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
