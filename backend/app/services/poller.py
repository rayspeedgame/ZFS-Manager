from __future__ import annotations

import asyncio
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import AppConfig
from app.core.state import state_store
from app.schemas.zfs_state import AppState, DatasetOverview, DiskOverview, PropertyValue, ZPoolOverview
from app.ssh.client import SSHClient, SSHConfig
from app.ssh.commands import DISK_OVERVIEW, ZFS_DATASET_OVERVIEW, ZPOOL_OVERVIEW
from app.ssh.parser import parse_command_output


class StatePoller:
    """Refresh the shared in-memory snapshot from SSH or local fixtures."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._interval_seconds = config.poller.interval_seconds
        self._task: asyncio.Task[None] | None = None
        self._backend_root = Path(__file__).resolve().parents[2]
        self._fixtures_dir = self._backend_root / "tests" / "fixtures"
        self._ssh_client = self._build_ssh_client() if config.poller.mode == "ssh" else None

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._run(), name="zfs-state-poller")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        if self._ssh_client is not None:
            await self._ssh_client.close()

    async def _run(self) -> None:
        while True:
            await self.refresh_once()
            await asyncio.sleep(self._interval_seconds)

    async def refresh_once(self) -> AppState:
        try:
            if self._config.poller.mode == "ssh":
                state = await self._refresh_from_ssh()
            else:
                state = await self._refresh_from_fixtures("Fixture mode is active.")
        except Exception as exc:
            if self._config.poller.fallback_to_fixture:
                state = await self._refresh_from_fixtures(
                    f"SSH refresh failed, serving fixture data instead: {exc}"
                )
                state.status = "degraded"
            else:
                state = AppState(
                    status="error",
                    message=f"State refresh failed: {exc}",
                    refresh_interval_seconds=self._interval_seconds,
                    last_updated=datetime.now(timezone.utc),
                )

        await state_store.set_state(state)
        return state

    async def _refresh_from_ssh(self) -> AppState:
        if self._ssh_client is None:
            raise RuntimeError("SSH mode is enabled but SSH client is not configured")

        # Keep all reads on the same SSH session to reduce handshake overhead.
        disk_raw = await self._ssh_client.run(
            DISK_OVERVIEW,
            timeout=self._config.ssh.command_timeout,
        )
        zpool_raw = await self._ssh_client.run(
            ZPOOL_OVERVIEW,
            timeout=self._config.ssh.command_timeout,
        )
        dataset_raw = await self._ssh_client.run(
            ZFS_DATASET_OVERVIEW,
            timeout=self._config.ssh.command_timeout,
        )

        return self._build_state(
            disk_data=parse_command_output(DISK_OVERVIEW, disk_raw),
            zpool_data=parse_command_output(ZPOOL_OVERVIEW, zpool_raw),
            dataset_data=parse_command_output(ZFS_DATASET_OVERVIEW, dataset_raw),
            status="ready",
            message="Live SSH data loaded successfully.",
        )

    async def _refresh_from_fixtures(self, message: str) -> AppState:
        # Fixture mode keeps the API usable while the real host integration is
        # still being configured or temporarily unavailable.
        disk_raw = self._read_fixture("disk_overview_sample.txt")
        zpool_raw = self._read_fixture("zpool_overview_sample.txt")
        dataset_raw = self._read_fixture("dataset_overview_sample.txt")

        return self._build_state(
            disk_data=parse_command_output(DISK_OVERVIEW, disk_raw),
            zpool_data=parse_command_output(ZPOOL_OVERVIEW, zpool_raw),
            dataset_data=parse_command_output(ZFS_DATASET_OVERVIEW, dataset_raw),
            status="ready",
            message=message,
        )

    def _build_state(
        self,
        *,
        disk_data: dict,
        zpool_data: dict,
        dataset_data: dict,
        status: str,
        message: str,
    ) -> AppState:
        return AppState(
            status=status,
            message=message,
            refresh_interval_seconds=self._interval_seconds,
            last_updated=datetime.now(timezone.utc),
            disk_overview=DiskOverview.model_validate(disk_data),
            zpool_overview=ZPoolOverview.model_validate(_normalize_property_values(zpool_data)),
            dataset_overview=DatasetOverview.model_validate(_normalize_property_values(dataset_data)),
        )

    def _build_ssh_client(self) -> SSHClient:
        ssh_config = SSHConfig(
            host=self._config.ssh.host,
            username=self._config.ssh.username,
            port=self._config.ssh.port,
            password=self._config.ssh.password,
            known_hosts=self._config.ssh.known_hosts,
            client_keys=self._config.ssh.key_files,
            connect_timeout=self._config.ssh.connect_timeout,
            keepalive_interval=self._config.ssh.keepalive_interval,
            keepalive_count_max=self._config.ssh.keepalive_count_max,
        )
        return SSHClient(ssh_config)

    def _read_fixture(self, filename: str) -> str:
        return (self._fixtures_dir / filename).read_text(encoding="utf-8")


def _normalize_property_values(payload: dict) -> dict:
    """Convert nested property dicts into Pydantic-friendly models."""
    normalized = dict(payload)
    properties = normalized.get("properties", {})
    converted: dict[str, dict[str, PropertyValue]] = {}

    for resource_name, property_map in properties.items():
        converted[resource_name] = {
            property_name: PropertyValue.model_validate(property_value)
            for property_name, property_value in property_map.items()
        }

    normalized["properties"] = converted
    return normalized
