from __future__ import annotations

from pydantic import BaseModel

from app.core.config import AppConfig


class SettingsSaveResponse(BaseModel):
    config: AppConfig
    config_path: str
    reloaded: bool = True
    message: str
