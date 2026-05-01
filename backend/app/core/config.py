from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class SSHSettings(BaseModel):
    host: str = "127.0.0.1"
    username: str = "root"
    port: int = 22
    password: str | None = None
    key_files: list[str] = Field(default_factory=list)
    known_hosts: str | None = None
    connect_timeout: float = 10.0
    command_timeout: float = 30.0
    keepalive_interval: float = 30.0
    keepalive_count_max: int = 3


class PollerSettings(BaseModel):
    mode: Literal["fixture", "ssh"] = "fixture"
    interval_seconds: int = 2
    fallback_to_fixture: bool = True
    tick_seconds: int = 1
    pools_interval_seconds: int = 5
    datasets_interval_seconds: int = 15
    disks_interval_seconds: int = 60
    properties_interval_seconds: int = 120


class AppConfig(BaseModel):
    poller: PollerSettings = Field(default_factory=PollerSettings)
    ssh: SSHSettings = Field(default_factory=SSHSettings)


def load_config() -> AppConfig:
    """Load config from backend/config.json, then apply env var overrides."""
    backend_root = Path(__file__).resolve().parents[2]
    config_path = Path(os.environ.get("ZFS_MANAGER_CONFIG", backend_root / "config.json"))

    data: dict = {}
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))

    config = AppConfig.model_validate(data)
    return _apply_env_overrides(config)


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    # Environment variables are convenient for Docker deployment.
    if value := os.environ.get("ZFS_MANAGER_POLLER_MODE"):
        config.poller.mode = value  # type: ignore[assignment]
    if value := os.environ.get("ZFS_MANAGER_POLLER_INTERVAL"):
        config.poller.interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_TICK"):
        config.poller.tick_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_FALLBACK"):
        config.poller.fallback_to_fixture = value.lower() in {"1", "true", "yes", "on"}
    if value := os.environ.get("ZFS_MANAGER_POLLER_POOLS_INTERVAL"):
        config.poller.pools_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_DATASETS_INTERVAL"):
        config.poller.datasets_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_DISKS_INTERVAL"):
        config.poller.disks_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_PROPERTIES_INTERVAL"):
        config.poller.properties_interval_seconds = int(value)

    if value := os.environ.get("ZFS_MANAGER_SSH_HOST"):
        config.ssh.host = value
    if value := os.environ.get("ZFS_MANAGER_SSH_USERNAME"):
        config.ssh.username = value
    if value := os.environ.get("ZFS_MANAGER_SSH_PORT"):
        config.ssh.port = int(value)
    if value := os.environ.get("ZFS_MANAGER_SSH_PASSWORD"):
        config.ssh.password = value
    if value := os.environ.get("ZFS_MANAGER_SSH_KNOWN_HOSTS"):
        config.ssh.known_hosts = value
    if value := os.environ.get("ZFS_MANAGER_SSH_CONNECT_TIMEOUT"):
        config.ssh.connect_timeout = float(value)
    if value := os.environ.get("ZFS_MANAGER_SSH_COMMAND_TIMEOUT"):
        config.ssh.command_timeout = float(value)
    if value := os.environ.get("ZFS_MANAGER_SSH_KEEPALIVE_INTERVAL"):
        config.ssh.keepalive_interval = float(value)
    if value := os.environ.get("ZFS_MANAGER_SSH_KEEPALIVE_COUNT_MAX"):
        config.ssh.keepalive_count_max = int(value)
    if value := os.environ.get("ZFS_MANAGER_SSH_KEY_FILES"):
        config.ssh.key_files = [item.strip() for item in value.split(",") if item.strip()]

    return config
