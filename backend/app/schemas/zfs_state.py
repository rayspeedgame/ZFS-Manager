from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field


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


class SummaryData(BaseModel):
    pool_count: int = 0
    unhealthy_pool_count: int = 0
    disk_count: int = 0
    dataset_count: int = 0
    total_allocated: int = 0
    total_free: int = 0


class SectionState(BaseModel):
    status: str = "idle"
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    error: str | None = None


class StateSections(BaseModel):
    disks: SectionState = Field(default_factory=SectionState)
    pools: SectionState = Field(default_factory=SectionState)
    datasets: SectionState = Field(default_factory=SectionState)


class AppMeta(BaseModel):
    app_status: str = "starting"
    source_status: str = "connecting"
    message: str = "Poller has not produced a snapshot yet."
    refresh_interval_seconds: int = 2
    refresh_plan_seconds: dict[str, int] = Field(default_factory=dict)
    last_updated: datetime | None = None
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    stale_seconds: int | None = None
    sections: StateSections = Field(default_factory=StateSections)


class AppData(BaseModel):
    summary: SummaryData = Field(default_factory=SummaryData)
    disks: list[dict[str, Any]] = Field(default_factory=list)
    pools: list[dict[str, Any]] = Field(default_factory=list)
    datasets: list[dict[str, Any]] = Field(default_factory=list)
    disk_overview: DiskOverview = Field(default_factory=DiskOverview)
    zpool_overview: ZPoolOverview = Field(default_factory=ZPoolOverview)
    dataset_overview: DatasetOverview = Field(default_factory=DatasetOverview)


class AppState(BaseModel):
    meta: AppMeta = Field(default_factory=AppMeta)
    data: AppData = Field(default_factory=AppData)

    @computed_field
    @property
    def status(self) -> str:
        return self.meta.app_status

    @computed_field
    @property
    def message(self) -> str:
        return self.meta.message

    @computed_field
    @property
    def refresh_interval_seconds(self) -> int:
        return self.meta.refresh_interval_seconds

    @computed_field
    @property
    def last_updated(self) -> datetime | None:
        return self.meta.last_updated

    @computed_field
    @property
    def disk_overview(self) -> DiskOverview:
        return self.data.disk_overview

    @computed_field
    @property
    def zpool_overview(self) -> ZPoolOverview:
        return self.data.zpool_overview

    @computed_field
    @property
    def dataset_overview(self) -> DatasetOverview:
        return self.data.dataset_overview
