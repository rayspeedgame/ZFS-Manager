from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


TopologyCategory = Literal["data", "log", "cache", "special", "dedup", "spare"]
TopologyLayout = Literal["stripe", "mirror", "raidz", "raidz2", "raidz3"]


class PoolTopologyAddItem(BaseModel):
    category: TopologyCategory
    layout: TopologyLayout = "stripe"
    devices: list[str] = Field(default_factory=list, min_length=1)

    @model_validator(mode="after")
    def validate_layout(self) -> "PoolTopologyAddItem":
        if self.category in {"cache", "spare"} and self.layout != "stripe":
            raise ValueError(f"{self.category} only supports stripe layout when adding devices.")
        if self.category in {"log", "special", "dedup"} and self.layout not in {"stripe", "mirror"}:
            raise ValueError(f"{self.category} only supports stripe or mirror layout when adding devices.")
        if self.layout != "stripe" and len(self.devices) < 2:
            raise ValueError(f"{self.layout} layout requires at least 2 devices.")
        if self.layout == "mirror" and len(self.devices) < 2:
            raise ValueError("mirror layout requires at least 2 devices.")
        if self.layout == "raidz" and len(self.devices) < 2:
            raise ValueError("raidz layout requires at least 2 devices.")
        if self.layout == "raidz2" and len(self.devices) < 3:
            raise ValueError("raidz2 layout requires at least 3 devices.")
        if self.layout == "raidz3" and len(self.devices) < 4:
            raise ValueError("raidz3 layout requires at least 4 devices.")
        return self


class PoolTopologyUpdateRequest(BaseModel):
    additions: list[PoolTopologyAddItem] = Field(default_factory=list)
    force: bool = False


class PoolTopologyUpdateResult(BaseModel):
    category: TopologyCategory
    layout: TopologyLayout
    devices: list[str] = Field(default_factory=list)
    success: bool
    message: str
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None


class PoolTopologyUpdateResponse(BaseModel):
    pool: str
    results: list[PoolTopologyUpdateResult] = Field(default_factory=list)
    refreshed: bool = False
    refresh_error: str | None = None
