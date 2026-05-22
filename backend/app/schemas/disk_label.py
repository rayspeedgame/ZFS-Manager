from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DiskLabelUpdateRequest(BaseModel):
    label: str = Field(default="")

    @field_validator("label")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        return value.strip()


class DiskLabelUpdateResponse(BaseModel):
    disk_key: str
    label: str
    refreshed: bool = True
    message: str
