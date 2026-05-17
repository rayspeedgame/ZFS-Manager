from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


DatasetCreateType = Literal["filesystem", "volume"]


class DatasetCreatePropertyItem(BaseModel):
    name: str = Field(min_length=1)
    value: str


class DatasetCreateRequest(BaseModel):
    parent: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: DatasetCreateType = "filesystem"
    properties: list[DatasetCreatePropertyItem] = Field(default_factory=list)

    @field_validator("parent", "name")
    @classmethod
    def validate_path_component(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be empty.")
        if any(char.isspace() for char in normalized):
            raise ValueError("Value cannot contain whitespace.")
        return normalized

    @model_validator(mode="after")
    def validate_properties(self) -> "DatasetCreateRequest":
        property_names = {property_item.name for property_item in self.properties}
        if self.type == "volume" and "volsize" not in property_names:
            raise ValueError("volsize is required when creating a zvol.")
        return self

    @property
    def full_name(self) -> str:
        return f"{self.parent}/{self.name}"


class DatasetCreateResponse(BaseModel):
    dataset: str
    success: bool
    message: str
    task_id: str | None = None
    command: str | None = None
    exit_status: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    refreshed: bool = False
    refresh_error: str | None = None
