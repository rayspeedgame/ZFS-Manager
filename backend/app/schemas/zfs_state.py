from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PropertyValue(BaseModel):
    value: Any = None
    source: str | None = None


class ZPoolStatusNode(BaseModel):
    name: str
    state: str
    read: int
    write: int
    cksum: int
    notes: str | None = None
    children: list["ZPoolStatusNode"] = Field(default_factory=list)


class ZPoolStatus(BaseModel):
    pool: str | None = None
    state: str | None = None
    scan: str | None = None
    config: list[ZPoolStatusNode] = Field(default_factory=list)
    errors: str | None = None


class DiskOverview(BaseModel):
    lsblk: dict[str, Any] = Field(default_factory=dict)
    findmnt: dict[str, Any] = Field(default_factory=dict)
    blkid: list[dict[str, Any]] = Field(default_factory=list)


class ZPoolOverview(BaseModel):
    status: ZPoolStatus = Field(default_factory=ZPoolStatus)
    pools: list[dict[str, Any]] = Field(default_factory=list)
    properties: dict[str, dict[str, PropertyValue]] = Field(default_factory=dict)


class DatasetOverview(BaseModel):
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    properties: dict[str, dict[str, PropertyValue]] = Field(default_factory=dict)


class AppState(BaseModel):
    # Keep top-level metadata explicit so Swagger shows the polling lifecycle.
    status: str = "starting"
    message: str = "Poller has not produced a snapshot yet."
    refresh_interval_seconds: int = 2
    last_updated: datetime | None = None
    disk_overview: DiskOverview = Field(default_factory=DiskOverview)
    zpool_overview: ZPoolOverview = Field(default_factory=ZPoolOverview)
    dataset_overview: DatasetOverview = Field(default_factory=DatasetOverview)
