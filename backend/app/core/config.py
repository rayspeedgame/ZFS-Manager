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
    # --- Active intervals (at least one WebSocket client connected) ---
    mode: Literal["fixture", "ssh"] = "fixture"
    fallback_to_fixture: bool = True
    tick_seconds: int = 1
    pools_interval_seconds: int = 5
    datasets_interval_seconds: int = 15
    disks_interval_seconds: int = 60
    properties_interval_seconds: int = 120
    # --- Idle intervals (no WebSocket clients connected) ---
    idle_tick_seconds: int = 30
    idle_pools_interval_seconds: int = 60
    idle_datasets_interval_seconds: int = 300
    idle_disks_interval_seconds: int = 600
    idle_properties_interval_seconds: int = 1200


class AuthSettings(BaseModel):
    enabled: bool = False
    password: str | None = None


class AppConfig(BaseModel):
    poller: PollerSettings = Field(default_factory=PollerSettings)
    ssh: SSHSettings = Field(default_factory=SSHSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    disk_labels: dict[str, str] = Field(default_factory=dict)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = BACKEND_ROOT / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.json"
DEFAULT_EXAMPLE_CONFIG_PATH = CONFIG_DIR / "config.example.json"
DEFAULT_TASK_DB_PATH = CONFIG_DIR / "tasks.sqlite3"
LEGACY_CONFIG_PATH = BACKEND_ROOT / "config.json"


def load_config() -> AppConfig:
    """Load config from disk, then apply environment variable overrides."""
    config_path = resolve_config_path()

    data: dict = {}
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding="utf-8"))

    config = AppConfig.model_validate(data)
    return _apply_env_overrides(config)


def resolve_config_path() -> Path:
    # Prefer an explicit override, then the managed config directory, and only
    # fall back to the legacy flat file for older local checkouts.
    if config_path := os.environ.get("ZFS_MANAGER_CONFIG"):
        return Path(config_path)
    if DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_CONFIG_PATH
    return LEGACY_CONFIG_PATH


def save_config(config: AppConfig) -> Path:
    config_path = resolve_config_path()
    # Once the app writes settings itself, keep them in backend/config/ even if
    # the current runtime had to fall back to the legacy location for reading.
    if config_path == LEGACY_CONFIG_PATH:
        config_path = DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        config.model_dump_json(indent=2) + "\n",
        encoding="utf-8",
    )
    return config_path


def resolve_task_db_path() -> Path:
    if db_path := os.environ.get("ZFS_MANAGER_TASK_DB"):
        return Path(db_path)
    return DEFAULT_TASK_DB_PATH


def _apply_env_overrides(config: AppConfig) -> AppConfig:
    # Environment variables are convenient for Docker deployment.
    if value := os.environ.get("ZFS_MANAGER_POLLER_MODE"):
        config.poller.mode = value  # type: ignore[assignment]
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
    if value := os.environ.get("ZFS_MANAGER_POLLER_IDLE_TICK"):
        config.poller.idle_tick_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_IDLE_POOLS_INTERVAL"):
        config.poller.idle_pools_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_IDLE_DATASETS_INTERVAL"):
        config.poller.idle_datasets_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_IDLE_DISKS_INTERVAL"):
        config.poller.idle_disks_interval_seconds = int(value)
    if value := os.environ.get("ZFS_MANAGER_POLLER_IDLE_PROPERTIES_INTERVAL"):
        config.poller.idle_properties_interval_seconds = int(value)

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

    if value := os.environ.get("ZFS_MANAGER_AUTH_ENABLED"):
        config.auth.enabled = value.lower() in {"1", "true", "yes", "on"}
    if value := os.environ.get("ZFS_MANAGER_AUTH_PASSWORD"):
        config.auth.password = value

    return config
