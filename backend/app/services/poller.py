from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from app.core.client_tracker import client_tracker
from app.core.config import AppConfig
from app.core.state import state_store
from app.schemas.zfs_state import (
    AppData,
    AppMeta,
    AppState,
    DatasetOverview,
    DiskOverview,
    PropertyValue,
    SectionState,
    StateSections,
    SummaryData,
    ZPoolOverview,
)
from app.ssh.client import SSHClient, SSHConfig
from app.ssh.commands import (
    DISK_OVERVIEW,
    ZFS_DATASET_CORE,
    ZFS_DATASET_OVERVIEW,
    ZFS_DATASET_PROPERTIES,
    ZPOOL_CORE,
    ZPOOL_OVERVIEW,
    ZPOOL_PROPERTIES,
)
from app.ssh.parser import parse_command_output


@dataclass(slots=True)
class CachedPayload:
    data: dict = field(default_factory=dict)
    last_attempt_at: datetime | None = None
    last_success_at: datetime | None = None
    error: str | None = None

    def has_data(self) -> bool:
        return bool(self.data)


@dataclass(slots=True)
class ScheduledRefresh:
    interval_seconds: int
    next_due_at: datetime = field(
        default_factory=lambda: datetime.min.replace(tzinfo=timezone.utc)
    )

    def is_due(self, current_time: datetime) -> bool:
        return current_time >= self.next_due_at

    def mark_completed(self, current_time: datetime) -> None:
        self.next_due_at = current_time + timedelta(seconds=self.interval_seconds)


class StatePoller:
    """Refresh the shared in-memory snapshot from SSH or local fixtures."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._active_tick = max(1, config.poller.tick_seconds)
        self._idle_tick = max(1, config.poller.idle_tick_seconds)
        self._task: asyncio.Task[None] | None = None
        self._backend_root = Path(__file__).resolve().parents[2]
        self._fixtures_dir = self._backend_root / "tests" / "fixtures"
        self._ssh_client = self._build_ssh_client() if config.poller.mode == "ssh" else None
        self._disk_cache = CachedPayload()
        self._zpool_core_cache = CachedPayload()
        self._zpool_properties_cache = CachedPayload()
        self._dataset_core_cache = CachedPayload()
        self._dataset_properties_cache = CachedPayload()
        # Start in idle mode — the poller loop will switch to active intervals
        # on the first tick once a WebSocket client connects.
        self._tick_seconds = self._idle_tick
        self._schedules = {
            "disks": ScheduledRefresh(max(1, config.poller.idle_disks_interval_seconds)),
            "pools": ScheduledRefresh(max(1, config.poller.idle_pools_interval_seconds)),
            "datasets": ScheduledRefresh(max(1, config.poller.idle_datasets_interval_seconds)),
            "properties": ScheduledRefresh(max(1, config.poller.idle_properties_interval_seconds)),
        }
        self._active_clients = False

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
        # Mode detection runs at a fixed 1-second cadence so active↔idle
        # transitions respond quickly even when the idle tick is very large.
        # The configurable _tick_seconds only gates how often refresh_once()
        # actually runs, not how often we check for mode changes.
        _MODE_CHECK_SECONDS = 1
        last_refresh_at = datetime.min.replace(tzinfo=timezone.utc)

        while True:
            now = datetime.now(timezone.utc)
            currently_active = client_tracker.active
            if currently_active != self._active_clients:
                self._apply_mode(currently_active)
                self._active_clients = currently_active

            if (now - last_refresh_at).total_seconds() >= self._tick_seconds:
                await self.refresh_once()
                last_refresh_at = datetime.now(timezone.utc)

            await asyncio.sleep(_MODE_CHECK_SECONDS)

    async def refresh_once(self, *, force_all: bool = False) -> AppState:
        attempt_at = datetime.now(timezone.utc)
        # Writes can bypass the schedule and request a full refresh immediately.
        due_jobs = list(self._schedules.keys()) if force_all else self._collect_due_jobs(attempt_at)

        if not due_jobs and self._has_cached_data():
            return await state_store.get_state()

        try:
            if self._config.poller.mode == "ssh":
                state = await self._refresh_from_ssh(attempt_at, due_jobs)
            else:
                state = await self._refresh_from_fixtures(
                    "Fixture mode is active.",
                    attempt_at,
                    due_jobs,
                )
        except Exception as exc:
            self._mark_failure(due_jobs, exc, attempt_at)

            if self._config.poller.mode == "ssh" and self._has_cached_data():
                state = self._build_state(
                    attempt_at=attempt_at,
                    app_status="degraded",
                    source_status="degraded",
                    message=f"Scheduled refresh failed for {', '.join(due_jobs)}: {exc}",
                )
            elif self._config.poller.fallback_to_fixture:
                state = await self._refresh_from_fixtures(
                    f"SSH refresh failed, serving fixture data instead: {exc}",
                    attempt_at,
                    list(self._schedules.keys()),
                )
                state.meta.app_status = "degraded"
                state.meta.source_status = "disconnected"
            else:
                state = self._build_state(
                    attempt_at=attempt_at,
                    app_status="error",
                    source_status="disconnected",
                    message=f"State refresh failed: {exc}",
                )

        await state_store.set_state(state)
        return state

    async def _refresh_from_ssh(self, attempt_at: datetime, due_jobs: list[str]) -> AppState:
        if self._ssh_client is None:
            raise RuntimeError("SSH mode is enabled but SSH client is not configured")

        successes: list[str] = []
        failures: list[str] = []

        for job_name in due_jobs:
            try:
                await self._refresh_ssh_job(job_name, attempt_at)
                successes.append(job_name)
            except Exception as exc:
                failures.append(job_name)
                self._mark_failure([job_name], exc, attempt_at)
            finally:
                self._schedules[job_name].mark_completed(attempt_at)

        source_status = "connected"
        if failures and successes:
            source_status = "degraded"
        elif failures and not successes:
            source_status = "disconnected" if not self._has_cached_data() else "degraded"

        app_status = _determine_app_status(self._section_states())
        message = _build_refresh_message(
            source="ssh",
            successes=successes,
            failures=failures,
        )

        return self._build_state(
            attempt_at=attempt_at,
            app_status=app_status,
            source_status=source_status,
            message=message,
        )

    async def _refresh_ssh_job(self, job_name: str, attempt_at: datetime) -> None:
        timeout = self._config.ssh.command_timeout

        if job_name == "disks":
            raw_output = await self._ssh_client.run(DISK_OVERVIEW, timeout=timeout)
            self._record_success(
                self._disk_cache,
                parse_command_output(DISK_OVERVIEW, raw_output),
                attempt_at,
            )
            return

        if job_name == "pools":
            raw_output = await self._ssh_client.run(ZPOOL_CORE, timeout=timeout)
            self._record_success(
                self._zpool_core_cache,
                parse_command_output(ZPOOL_CORE, raw_output),
                attempt_at,
            )
            return

        if job_name == "datasets":
            raw_output = await self._ssh_client.run(ZFS_DATASET_CORE, timeout=timeout)
            self._record_success(
                self._dataset_core_cache,
                parse_command_output(ZFS_DATASET_CORE, raw_output),
                attempt_at,
            )
            return

        if job_name == "properties":
            zpool_properties_raw = await self._ssh_client.run(ZPOOL_PROPERTIES, timeout=timeout)
            dataset_properties_raw = await self._ssh_client.run(
                ZFS_DATASET_PROPERTIES,
                timeout=timeout,
            )
            self._record_success(
                self._zpool_properties_cache,
                parse_command_output(ZPOOL_PROPERTIES, zpool_properties_raw),
                attempt_at,
            )
            self._record_success(
                self._dataset_properties_cache,
                parse_command_output(ZFS_DATASET_PROPERTIES, dataset_properties_raw),
                attempt_at,
            )
            return

        raise ValueError(f"Unknown refresh job: {job_name}")

    async def _refresh_from_fixtures(
        self,
        message: str,
        attempt_at: datetime,
        due_jobs: list[str],
    ) -> AppState:
        fixture_messages: list[str] = []

        if "disks" in due_jobs:
            disk_raw = self._read_fixture("disk_overview_sample.txt")
            self._record_success(
                self._disk_cache,
                parse_command_output(DISK_OVERVIEW, disk_raw),
                attempt_at,
            )
            self._schedules["disks"].mark_completed(attempt_at)
            fixture_messages.append("disks")

        if "pools" in due_jobs or "properties" in due_jobs:
            zpool_raw = self._read_fixture("zpool_overview_sample.txt")
            zpool_payload = parse_command_output(ZPOOL_OVERVIEW, zpool_raw)
            if "pools" in due_jobs:
                self._record_success(
                    self._zpool_core_cache,
                    {
                        "status": zpool_payload.get("status", {}),
                        "pools": zpool_payload.get("pools", []),
                    },
                    attempt_at,
                )
                self._schedules["pools"].mark_completed(attempt_at)
                fixture_messages.append("pools")
            if "properties" in due_jobs:
                self._record_success(
                    self._zpool_properties_cache,
                    {"properties": zpool_payload.get("properties", {})},
                    attempt_at,
                )
                self._schedules["properties"].mark_completed(attempt_at)
                fixture_messages.append("properties")

        if "datasets" in due_jobs or "properties" in due_jobs:
            dataset_raw = self._read_fixture("dataset_overview_sample.txt")
            dataset_payload = parse_command_output(ZFS_DATASET_OVERVIEW, dataset_raw)
            if "datasets" in due_jobs:
                self._record_success(
                    self._dataset_core_cache,
                    {"datasets": dataset_payload.get("datasets", [])},
                    attempt_at,
                )
                self._schedules["datasets"].mark_completed(attempt_at)
                fixture_messages.append("datasets")
            if "properties" in due_jobs:
                self._record_success(
                    self._dataset_properties_cache,
                    {"properties": dataset_payload.get("properties", {})},
                    attempt_at,
                )

        return self._build_state(
            attempt_at=attempt_at,
            app_status="ready",
            source_status="fixture",
            message=message if not fixture_messages else f"{message} Refreshed {', '.join(fixture_messages)}.",
        )

    def _collect_due_jobs(self, attempt_at: datetime) -> list[str]:
        return [
            job_name
            for job_name, schedule in self._schedules.items()
            if schedule.is_due(attempt_at)
        ]

    def _apply_mode(self, active: bool) -> None:
        """Switch schedule intervals between active (fast) and idle (slow)."""
        if active:
            self._schedules["disks"].interval_seconds = max(1, self._config.poller.disks_interval_seconds)
            self._schedules["pools"].interval_seconds = max(1, self._config.poller.pools_interval_seconds)
            self._schedules["datasets"].interval_seconds = max(1, self._config.poller.datasets_interval_seconds)
            self._schedules["properties"].interval_seconds = max(1, self._config.poller.properties_interval_seconds)
            self._tick_seconds = self._active_tick
            # On idle→active transition, reset all schedules to trigger an
            # immediate full refresh so the newly connected browser gets fresh
            # data without waiting for the next due window.
            now = datetime.now(timezone.utc)
            for schedule in self._schedules.values():
                schedule.next_due_at = now
        else:
            self._schedules["disks"].interval_seconds = max(1, self._config.poller.idle_disks_interval_seconds)
            self._schedules["pools"].interval_seconds = max(1, self._config.poller.idle_pools_interval_seconds)
            self._schedules["datasets"].interval_seconds = max(1, self._config.poller.idle_datasets_interval_seconds)
            self._schedules["properties"].interval_seconds = max(1, self._config.poller.idle_properties_interval_seconds)
            self._tick_seconds = self._idle_tick

    def _build_state(
        self,
        *,
        attempt_at: datetime,
        app_status: str,
        source_status: str,
        message: str,
    ) -> AppState:
        disk_data = self._disk_cache.data
        zpool_data = _merge_payloads(self._zpool_core_cache.data, self._zpool_properties_cache.data)
        dataset_data = _merge_payloads(self._dataset_core_cache.data, self._dataset_properties_cache.data)

        last_success_at = _latest_timestamp(
            self._disk_cache.last_success_at,
            self._zpool_core_cache.last_success_at,
            self._zpool_properties_cache.last_success_at,
            self._dataset_core_cache.last_success_at,
            self._dataset_properties_cache.last_success_at,
        )
        stale_seconds = None
        if last_success_at is not None:
            stale_seconds = max(0, int((attempt_at - last_success_at).total_seconds()))

        section_states = self._section_states()

        disks = _build_disk_rows(disk_data, dataset_data, zpool_data, self._config.disk_labels)

        return AppState(
            meta=AppMeta(
                app_status=app_status,
                source_status=source_status,
                message=message,
                refresh_interval_seconds=self._tick_seconds,
                refresh_plan_seconds={
                    "tick": self._tick_seconds,
                    "disks": self._schedules["disks"].interval_seconds,
                    "pools": self._schedules["pools"].interval_seconds,
                    "datasets": self._schedules["datasets"].interval_seconds,
                    "properties": self._schedules["properties"].interval_seconds,
                },
                last_updated=attempt_at,
                last_attempt_at=attempt_at,
                last_success_at=last_success_at,
                stale_seconds=stale_seconds,
                sections=StateSections(
                    disks=section_states["disks"],
                    pools=section_states["pools"],
                    datasets=section_states["datasets"],
                ),
            ),
            data=AppData(
                summary=_build_summary(zpool_data, disk_data, dataset_data),
                disks=disks,
                pools=_build_pool_rows(zpool_data, disks),
                datasets=_build_dataset_rows(dataset_data),
                disk_overview=DiskOverview.model_validate(disk_data),
                zpool_overview=ZPoolOverview.model_validate(_normalize_property_values(zpool_data)),
                dataset_overview=DatasetOverview.model_validate(_normalize_property_values(dataset_data)),
            ),
        )

    def _section_states(self) -> dict[str, SectionState]:
        return {
            "disks": _to_section_state([self._disk_cache]),
            "pools": _to_section_state([self._zpool_core_cache, self._zpool_properties_cache]),
            "datasets": _to_section_state([self._dataset_core_cache, self._dataset_properties_cache]),
        }

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

    def _has_cached_data(self) -> bool:
        return any(
            cache.has_data()
            for cache in (
                self._disk_cache,
                self._zpool_core_cache,
                self._zpool_properties_cache,
                self._dataset_core_cache,
                self._dataset_properties_cache,
            )
        )

    def _mark_failure(self, job_names: list[str], exc: Exception, attempt_at: datetime) -> None:
        error_message = str(exc)
        for job_name in job_names:
            for cache in self._job_caches(job_name):
                cache.last_attempt_at = attempt_at
                cache.error = error_message

    def _job_caches(self, job_name: str) -> list[CachedPayload]:
        if job_name == "disks":
            return [self._disk_cache]
        if job_name == "pools":
            return [self._zpool_core_cache]
        if job_name == "datasets":
            return [self._dataset_core_cache]
        if job_name == "properties":
            return [self._zpool_properties_cache, self._dataset_properties_cache]
        raise ValueError(f"Unknown refresh job: {job_name}")

    @staticmethod
    def _record_success(cache: CachedPayload, payload: dict, attempted_at: datetime) -> None:
        cache.data = payload
        cache.last_attempt_at = attempted_at
        cache.last_success_at = attempted_at
        cache.error = None


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


def _merge_payloads(*payloads: dict) -> dict:
    merged: dict = {}
    for payload in payloads:
        merged.update(payload)
    return merged


def _to_section_state(caches: list[CachedPayload]) -> SectionState:
    attempted_at = _latest_timestamp(*(cache.last_attempt_at for cache in caches))
    success_at = _latest_timestamp(*(cache.last_success_at for cache in caches))
    errors = [cache.error for cache in caches if cache.error]

    if attempted_at is None and success_at is None:
        status = "idle"
    elif errors and success_at is None:
        status = "error"
    elif errors:
        status = "stale"
    else:
        status = "ready"

    return SectionState(
        status=status,
        last_attempt_at=attempted_at,
        last_success_at=success_at,
        error="; ".join(dict.fromkeys(errors)) if errors else None,
    )


def _latest_timestamp(*timestamps: datetime | None) -> datetime | None:
    values = [timestamp for timestamp in timestamps if timestamp is not None]
    if not values:
        return None
    return max(values)


def _determine_app_status(section_states: dict[str, SectionState]) -> str:
    statuses = [section.status for section in section_states.values()]
    if all(status == "ready" for status in statuses):
        return "ready"
    if any(status in {"ready", "stale"} for status in statuses):
        return "degraded"
    return "error"


def _build_refresh_message(*, source: str, successes: list[str], failures: list[str]) -> str:
    fragments: list[str] = []
    if successes:
        fragments.append(f"Updated {', '.join(successes)}")
    if failures:
        fragments.append(f"Failed {', '.join(failures)}")
    if not fragments:
        return f"No scheduled {source} refresh was due."
    prefix = "Live SSH refresh" if source == "ssh" else "Fixture refresh"
    return f"{prefix}: {'; '.join(fragments)}."


def _build_summary(zpool_data: dict, disk_data: dict, dataset_data: dict) -> SummaryData:
    pools = zpool_data.get("pools", [])
    disks = disk_data.get("lsblk", {}).get("blockdevices", [])
    datasets = dataset_data.get("datasets", [])

    return SummaryData(
        pool_count=len(pools),
        unhealthy_pool_count=sum(1 for pool in pools if pool.get("health") != "ONLINE"),
        disk_count=len(disks),
        dataset_count=len(datasets),
        total_allocated=sum(int(pool.get("allocated") or 0) for pool in pools),
        total_free=sum(int(pool.get("free") or 0) for pool in pools),
    )


def _build_disk_rows(
    disk_data: dict,
    dataset_data: dict,
    zpool_data: dict,
    disk_labels: dict[str, str] | None = None,
) -> list[dict]:
    devices = disk_data.get("lsblk", {}).get("blockdevices", [])
    blkid_rows = disk_data.get("blkid", [])
    by_id_rows = disk_data.get("by_id", [])
    # zpool status usually reports by-id paths while lsblk reports kernel paths.
    # Build both alias and parent-disk maps first so pool membership can be
    # resolved back to the correct whole disk row.
    by_id_alias_map = _build_by_id_alias_map(by_id_rows)
    partition_parent_map = _build_partition_parent_map(devices)
    topology_membership = _build_topology_membership_map(
        zpool_data,
        by_id_alias_map=by_id_alias_map,
        partition_parent_map=partition_parent_map,
    )
    rows: list[dict] = []
    for device in devices:
        disk_path = device.get("path") or f"/dev/{device.get('name')}"
        disk_id = _resolve_disk_id(device_path=disk_path, by_id_rows=by_id_rows)
        disk_key = _resolve_disk_key(disk_path=disk_path, disk_id=disk_id)
        by_id_paths = _resolve_by_id_paths(device_path=disk_path, by_id_rows=by_id_rows)
        preferred_by_id_path = _preferred_by_id_path(by_id_paths)
        custom_name = str((disk_labels or {}).get(disk_key) or "").strip() or None
        display_name = custom_name or str(disk_path)
        children = device.get("children") or []
        partitions = [
            _build_partition_row(
                partition=child,
                parent_device=device,
                parent_display_name=display_name,
                blkid_rows=blkid_rows,
                by_id_rows=by_id_rows,
                topology_membership=topology_membership,
                by_id_alias_map=by_id_alias_map,
                partition_parent_map=partition_parent_map,
            )
            for child in children
        ]
        primary_partition = partitions[0] if partitions else {}
        primary_pool_name = primary_partition.get("poolName")
        primary_filesystem = primary_partition.get("filesystem")
        device_pool_name = _resolve_disk_pool_name(
            device=device,
            primary_partition=primary_partition,
            topology_membership=topology_membership,
            by_id_alias_map=by_id_alias_map,
            partition_parent_map=partition_parent_map,
        )
        filesystem = primary_filesystem or _filesystem_from_device(
            device=device,
            blkid_rows=blkid_rows,
        )

        rows.append(
            {
                **device,
                "diskPath": disk_path,
                "kernelPath": disk_path,
                "diskId": disk_id,
                "diskKey": disk_key,
                "byIdPath": preferred_by_id_path,
                "byIdPaths": by_id_paths,
                "customName": custom_name,
                "displayName": display_name,
                "commandPath": preferred_by_id_path or disk_path,
                "aliases": _build_disk_aliases(
                    display_name=display_name,
                    kernel_path=disk_path,
                    by_id_paths=by_id_paths,
                ),
                "filesystem": filesystem or "-",
                "filesystemDisplay": _format_filesystem_display(filesystem or "-", device_pool_name or primary_pool_name or "-"),
                "poolName": device_pool_name or primary_pool_name or "-",
                "partitionPath": primary_partition.get("path") or "-",
                "partitions": partitions,
            }
        )

    return rows


def _build_pool_rows(zpool_data: dict, disks: list[dict]) -> list[dict]:
    pools = zpool_data.get("pools", [])
    properties = zpool_data.get("properties", {})
    status_by_pool = zpool_data.get("status_by_pool", {})
    disk_lookup = _build_disk_lookup(disks)
    rows: list[dict] = []

    for pool in pools:
        name = pool.get("name")
        status = _annotate_topology_status(status_by_pool.get(name) or {})
        available_topology_devices = _build_available_topology_devices(disks)
        rows.append(
            {
                **pool,
                "status": _enrich_topology_status(status, disk_lookup),
                "scanStatus": _build_scan_status(status.get("scan")),
                "expandStatus": _build_expand_status(status.get("expand")),
                "properties": properties.get(name, {}),
                "topologySummary": _build_topology_summary(status, disk_lookup, available_topology_devices),
                "removalTargets": _build_removal_targets(status, disk_lookup),
                "availableTopologyDevices": available_topology_devices,
            }
        )

    return rows


def _build_scan_status(scan: str | None) -> dict:
    normalized = str(scan or "").strip()
    lowered = normalized.lower()
    progress_match = re.search(r"([0-9]+(?:\.[0-9]+)?)%\s+done", normalized, re.IGNORECASE)
    eta_match = re.search(r",\s*([^,]+?)\s+to go", normalized, re.IGNORECASE)
    progress = 0
    if progress_match:
        progress = max(0, min(100, int(float(progress_match.group(1)))))
    elif "repaired" in lowered or "resilvered" in lowered:
        progress = 100
    elif "in progress" in lowered:
        progress = 15

    return {
        "raw": normalized or None,
        "active": "in progress" in lowered,
        "kind": (
            "scrub"
            if "scrub" in lowered
            else "resilver" if "resilver" in lowered else "expansion" if "expand" in lowered or "expansion" in lowered else None
        ),
        "progress": progress,
        "eta": eta_match.group(1).strip() if eta_match else None,
        "completed": (
            "scrub repaired" in lowered
            or "scrub completed" in lowered
            or ("resilvered" in lowered and "in progress" not in lowered)
        ),
        "stopped": (
            "scrub canceled" in lowered
            or "scrub cancelled" in lowered
            or "scrub stopped" in lowered
            or "resilver canceled" in lowered
            or "resilver cancelled" in lowered
            or "resilver stopped" in lowered
        ),
    }


def _build_expand_status(expand: str | None) -> dict:
    normalized = str(expand or "").strip()
    lowered = normalized.lower()
    progress_match = re.search(r"([0-9]+(?:\.[0-9]+)?)%\s+done", normalized, re.IGNORECASE)
    eta_match = re.search(r",\s*([^,]+?)\s+to go", normalized, re.IGNORECASE)
    progress = 0
    if progress_match:
        progress = max(0, min(100, int(float(progress_match.group(1)))))
    elif "expanded" in lowered and "in progress" not in lowered:
        progress = 100
    elif "in progress" in lowered:
        progress = 15

    return {
        "raw": normalized or None,
        "active": "in progress" in lowered,
        "kind": "expansion" if normalized else None,
        "progress": progress,
        "eta": eta_match.group(1).strip() if eta_match else None,
        "completed": "expanded" in lowered and "in progress" not in lowered,
        "stopped": "canceled" in lowered or "cancelled" in lowered or "stopped" in lowered,
    }


def _build_dataset_rows(dataset_data: dict) -> list[dict]:
    datasets = dataset_data.get("datasets", [])
    properties = dataset_data.get("properties", {})
    by_name: dict[str, dict] = {}

    for dataset in datasets:
        name = str(dataset.get("name") or "")
        dataset_properties = properties.get(name, {})
        by_name[name] = {
            **dataset,
            "poolName": _derive_dataset_pool_name(name),
            "parentName": _find_dataset_parent_name(name),
            "depth": _derive_dataset_depth(name),
            "shortName": _derive_dataset_short_name(name),
            "properties": dataset_properties,
            "sourceSummary": _get_property_source_summary(dataset_properties),
            "children": [],
        }

    # Build the hierarchy once on the backend so the frontend can render a
    # stable tree without re-deriving parent/child order from raw names.
    root_rows: list[dict] = []
    for row in by_name.values():
        parent_name = str(row.get("parentName") or "")
        parent = by_name.get(parent_name)
        if parent:
            parent.setdefault("children", []).append(row)
        else:
            root_rows.append(row)

    def sort_rows(items: list[dict]) -> list[dict]:
        return sorted(
            items,
            key=lambda item: (
                str(item.get("poolName") or ""),
                _dataset_type_rank(str(item.get("type") or "")),
                str(item.get("name") or ""),
            ),
        )

    def flatten(row: dict) -> list[dict]:
        # Keep each parent immediately followed by its descendants.
        ordered = [{key: value for key, value in row.items() if key != "children"}]
        for child in sort_rows(list(row.get("children") or [])):
            ordered.extend(flatten(child))
        return ordered

    ordered_rows: list[dict] = []
    for root in sort_rows(root_rows):
        ordered_rows.extend(flatten(root))

    return ordered_rows


def _find_dataset_parent_name(name: str) -> str:
    normalized = str(name or "")
    if not normalized:
        return ""
    if "@" in normalized:
        return normalized.split("@", 1)[0]
    if "/" in normalized:
        return normalized.rsplit("/", 1)[0]
    return ""


def _derive_dataset_pool_name(name: str) -> str:
    normalized = str(name or "")
    if not normalized:
        return "-"
    base_name = normalized.split("@", 1)[0]
    return base_name.split("/", 1)[0]


def _derive_dataset_short_name(name: str) -> str:
    normalized = str(name or "")
    if not normalized:
        return "-"
    if "@" in normalized:
        return f"@{normalized.split('@', 1)[1]}"
    return normalized.rsplit("/", 1)[-1]


def _derive_dataset_depth(name: str) -> int:
    normalized = str(name or "")
    if not normalized:
        return 0
    if "@" in normalized:
        return _derive_dataset_depth(normalized.split("@", 1)[0]) + 1
    return max(0, normalized.count("/"))


def _dataset_type_rank(dataset_type: str) -> int:
    normalized = str(dataset_type or "")
    if normalized == "filesystem":
        return 0
    if normalized == "volume":
        return 1
    if normalized == "snapshot":
        return 2
    return 3


def _get_property_source_summary(properties: dict[str, dict]) -> str:
    sources = [item.get("source") for item in properties.values() if item.get("source")]
    if not sources:
        return "Unknown"

    inherited_only = all(str(source).startswith("inherited from") for source in sources)
    local_only = all(source == "local" for source in sources)
    if local_only:
        return "Local"
    if inherited_only:
        return "Inherited"
    return "Mixed"


def _build_partition_row(
    partition: dict,
    parent_device: dict,
    parent_display_name: str,
    blkid_rows: list[dict],
    by_id_rows: list[dict],
    topology_membership: dict[str, str],
    by_id_alias_map: dict[str, str],
    partition_parent_map: dict[str, str],
) -> dict:
    partition_path = partition.get("path")
    blkid = next((item for item in blkid_rows if item.get("device") == partition_path), None)
    filesystem = (blkid or {}).get("type") or "-"
    partition_by_id_paths = _resolve_by_id_paths(device_path=partition_path, by_id_rows=by_id_rows)
    # Keep both partition-level and parent-disk by-id aliases. Pool topology,
    # task metadata, and recovery logic do not always report the same form.
    parent_by_id_paths = _resolve_by_id_paths(device_path=parent_device.get("path"), by_id_rows=by_id_rows)
    preferred_partition_by_id = _preferred_by_id_path(partition_by_id_paths)
    pool_name = _lookup_pool_name(
        partition_path,
        partition.get("name"),
        topology_membership,
        by_id_alias_map=by_id_alias_map,
        partition_parent_map=partition_parent_map,
    )

    return {
        **partition,
        "diskPath": parent_device.get("path") or f"/dev/{parent_device.get('name')}",
        "kernelPath": partition_path,
        # Some pools expose partition leaves while the effective capacity is
        # still determined by the parent disk. Keep both so maintenance
        # features can fall back when lsblk omits a partition size.
        "size": partition.get("size") or parent_device.get("size"),
        "parentSize": parent_device.get("size"),
        "diskId": _resolve_disk_id(parent_device.get("path"), by_id_rows),
        "byIdPath": preferred_partition_by_id,
        "byIdPaths": partition_by_id_paths,
        "parentByIdPaths": parent_by_id_paths,
        "displayName": parent_display_name,
        "commandPath": preferred_partition_by_id or partition_path,
        "aliases": _build_disk_aliases(
            display_name=parent_display_name,
            kernel_path=partition_path,
            # Pool topology can expose either the partition alias or the
            # parent whole-disk alias for the same physical member. Keep both
            # on partition-backed members so task recovery can recognize the
            # device regardless of which form the command or status uses.
            by_id_paths=[*partition_by_id_paths, *parent_by_id_paths],
        ),
        "filesystem": filesystem,
        "filesystemDisplay": _format_filesystem_display(filesystem, pool_name or "-"),
        "poolName": pool_name or "-",
    }


def _build_topology_membership_map(
    zpool_data: dict,
    *,
    by_id_alias_map: dict[str, str],
    partition_parent_map: dict[str, str],
) -> dict[str, str]:
    membership: dict[str, str] = {}
    status_by_pool = zpool_data.get("status_by_pool", {})

    def visit(node: dict, pool_name: str) -> None:
        name = node.get("name")
        if name:
            for candidate in _expanded_device_identity_candidates(
                name,
                name,
                by_id_alias_map=by_id_alias_map,
                partition_parent_map=partition_parent_map,
            ):
                membership[candidate] = pool_name
        for child in node.get("children", []):
            visit(child, pool_name)

    for pool_name, status in status_by_pool.items():
        for node in status.get("config", []):
            visit(node, str(pool_name))

    return membership


def _resolve_disk_pool_name(
    *,
    device: dict,
    primary_partition: dict,
    topology_membership: dict[str, str],
    by_id_alias_map: dict[str, str],
    partition_parent_map: dict[str, str],
) -> str | None:
    device_pool_name = _lookup_pool_name(
        device.get("path"),
        device.get("name"),
        topology_membership,
        by_id_alias_map=by_id_alias_map,
        partition_parent_map=partition_parent_map,
    )
    if device_pool_name:
        return device_pool_name
    if primary_partition.get("poolName") and primary_partition.get("poolName") != "-":
        return str(primary_partition["poolName"])
    return None


def _filesystem_from_device(*, device: dict, blkid_rows: list[dict]) -> str:
    device_path = device.get("path")
    blkid = next((item for item in blkid_rows if item.get("device") == device_path), None)
    return (blkid or {}).get("type") or "-"


def _format_filesystem_display(filesystem: str | None, pool_name: str | None) -> str:
    normalized_fs = str(filesystem or "-")
    normalized_pool = str(pool_name or "-")
    if normalized_fs.lower() == "zfs_member" and normalized_pool == "-":
        return "zfs_member (inactive)"
    return normalized_fs


def _lookup_pool_name(
    path: str | None,
    name: str | None,
    topology_membership: dict[str, str],
    *,
    by_id_alias_map: dict[str, str],
    partition_parent_map: dict[str, str],
) -> str | None:
    for candidate in _expanded_device_identity_candidates(
        path,
        name,
        by_id_alias_map=by_id_alias_map,
        partition_parent_map=partition_parent_map,
    ):
        if candidate in topology_membership:
            return topology_membership[candidate]
    return None


def _build_by_id_alias_map(by_id_rows: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for row in by_id_rows:
        alias = str(row.get("id") or "").strip()
        path = str(row.get("path") or "").strip()
        if not alias or not path:
            continue
        mapping[alias] = path
        mapping[f"/dev/disk/by-id/{alias}"] = path
    return mapping


def _build_partition_parent_map(devices: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for device in devices:
        parent_path = str(device.get("path") or f"/dev/{device.get('name') or ''}").strip()
        if not parent_path:
            continue
        for child in device.get("children") or []:
            child_path = str(child.get("path") or f"/dev/{child.get('name') or ''}").strip()
            child_name = str(child.get("name") or "").strip()
            if child_path:
                mapping[child_path] = parent_path
                if child_path.startswith("/dev/"):
                    mapping[child_path.removeprefix("/dev/")] = parent_path
            if child_name:
                mapping[child_name] = parent_path
    return mapping


def _device_identity_candidates(path: str | None, name: str | None) -> list[str]:
    candidates: list[str] = []
    for value in (path, name):
        if not value:
            continue
        text = str(value)
        candidates.append(text)
        if "/" in text:
            candidates.append(text.rsplit("/", 1)[-1])
        if text.startswith("/dev/"):
            candidates.append(text.removeprefix("/dev/"))
    return list(dict.fromkeys(candidates))


def _expanded_device_identity_candidates(
    path: str | None,
    name: str | None,
    *,
    by_id_alias_map: dict[str, str],
    partition_parent_map: dict[str, str],
) -> list[str]:
    # A single topology member may appear as a by-id alias, a partition path,
    # or a whole-disk path depending on which command produced it. Expand every
    # candidate into the equivalent aliases before matching pool membership.
    pending = list(_device_identity_candidates(path, name))
    seen: list[str] = []

    while pending:
        candidate = pending.pop(0)
        if not candidate or candidate in seen:
            continue
        seen.append(candidate)

        resolved_target = by_id_alias_map.get(candidate)
        if resolved_target:
            pending.extend(_device_identity_candidates(resolved_target, resolved_target))

        parent_target = partition_parent_map.get(candidate)
        if parent_target:
            pending.extend(_device_identity_candidates(parent_target, parent_target))

    return seen


def _resolve_disk_id(device_path: str | None, by_id_rows: list[dict]) -> str:
    if device_path:
        direct_matches = [row.get("id") for row in by_id_rows if row.get("path") == device_path]
        non_partition_matches = [item for item in direct_matches if item and "-part" not in item]
        if non_partition_matches:
            return str(non_partition_matches[0])
        if direct_matches:
            return str(direct_matches[0])
    return str(device_path or "-")


def _resolve_disk_key(*, disk_path: str, disk_id: str) -> str:
    normalized_id = str(disk_id or "").strip()
    if normalized_id and normalized_id != "-":
        return normalized_id
    return str(disk_path or "-")


def _resolve_by_id_paths(*, device_path: str | None, by_id_rows: list[dict]) -> list[str]:
    if not device_path:
        return []
    aliases = [
        f"/dev/disk/by-id/{row.get('id')}"
        for row in by_id_rows
        if row.get("path") == device_path and row.get("id")
    ]
    return list(dict.fromkeys(str(alias) for alias in aliases if alias))


def _preferred_by_id_path(by_id_paths: list[str]) -> str | None:
    if not by_id_paths:
        return None
    non_partition = [path for path in by_id_paths if "-part" not in path]
    if non_partition:
        return sorted(non_partition)[0]
    return sorted(by_id_paths)[0]


def _build_disk_aliases(*, display_name: str, kernel_path: str, by_id_paths: list[str]) -> list[str]:
    aliases = [display_name, kernel_path, *by_id_paths]
    return list(dict.fromkeys(alias for alias in aliases if alias))


def _build_disk_lookup(disks: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for disk in disks:
        _register_device_identity(lookup, disk)
        for partition in disk.get("partitions", []):
            partition_entry = {
                **partition,
                "size": partition.get("size") or disk.get("size"),
                "parentSize": disk.get("size"),
                "diskId": disk.get("diskId"),
                "model": disk.get("model"),
                "diskPath": disk.get("diskPath") or disk.get("path"),
            }
            _register_device_identity(lookup, partition_entry)
    return lookup


def _register_device_identity(lookup: dict[str, dict], device: dict) -> None:
    path = device.get("path")
    name = device.get("name")
    for candidate in _device_identity_candidates(path, name):
        lookup[candidate] = device
    for alias in device.get("byIdPaths") or []:
        for candidate in _device_identity_candidates(alias, alias):
            lookup[candidate] = device


def _enrich_topology_status(status: dict, disk_lookup: dict[str, dict]) -> dict:
    if not status:
        return {}

    return {
        **status,
        "config": [_enrich_topology_node(node, disk_lookup) for node in status.get("config", [])],
    }


def _enrich_topology_node(node: dict, disk_lookup: dict[str, dict]) -> dict:
    device = _lookup_topology_device(node.get("name"), disk_lookup)
    enriched = {
        **node,
        "children": [_enrich_topology_node(child, disk_lookup) for child in node.get("children", [])],
    }
    if device:
        # Keep the raw member name from `zpool status -L` for diagnostics while
        # also exposing the preferred command target for operations. This lets
        # the UI show friendly aliases without losing the exact topology token
        # that ZFS reported in the latest snapshot.
        enriched["statusName"] = node.get("name")
        enriched["commandTarget"] = device.get("commandPath") or device.get("diskPath") or device.get("path") or node.get("name")
        enriched["devicePath"] = enriched["commandTarget"]
        enriched["displayName"] = device.get("displayName") or device.get("diskPath") or device.get("path") or node.get("name")
        enriched["diskId"] = device.get("diskId") or enriched["devicePath"]
        enriched["kernelPath"] = device.get("kernelPath") or device.get("diskPath") or device.get("path")
        enriched["byIdPath"] = device.get("byIdPath")
        enriched["deviceModel"] = device.get("model")
        enriched["aliases"] = device.get("aliases") or [enriched["displayName"]]
    elif not enriched.get("displayName"):
        enriched["displayName"] = enriched.get("name")
    return enriched


def _lookup_topology_device(name: str | None, disk_lookup: dict[str, dict]) -> dict | None:
    for candidate in _device_identity_candidates(name, name):
        if candidate in disk_lookup:
            return disk_lookup[candidate]
    return None


def _build_topology_summary(status: dict, disk_lookup: dict[str, dict], available_devices: list[dict]) -> list[dict]:
    config = status.get("config", []) if status else []
    if not config:
        return []

    root = config[0]
    scan_status = _build_scan_status(status.get("scan"))
    groups: list[dict] = []
    for group_name in ("data", "log", "cache", "special", "dedup", "spare"):
        nodes = [node for node in _collect_topology_group_nodes(root, group_name) if node.get("vdev_class") == group_name]
        groups.append(
            {
                "name": group_name,
                "label": _topology_group_label(group_name),
                "items": [
                    _build_topology_summary_item(
                        node,
                        disk_lookup,
                        available_devices,
                        scan_active=bool(scan_status.get("active")),
                    )
                    for node in nodes
                ],
            }
        )
    return groups


def _build_removal_targets(status: dict, disk_lookup: dict[str, dict]) -> list[dict]:
    config = status.get("config", []) if status else []
    if not config:
        return []

    root = config[0]
    targets: list[dict] = []
    for group_name in ("data", "log", "cache", "special", "dedup", "spare"):
        nodes = [node for node in _collect_topology_group_nodes(root, group_name) if node.get("vdev_class") == group_name]
        targets.extend(_build_removal_target(node, disk_lookup) for node in nodes)
    return targets


def _collect_topology_group_nodes(root: dict, group_name: str) -> list[dict]:
    children = root.get("children", []) or []
    if group_name == "data":
        return [child for child in children if child.get("vdev_class") == group_name]

    group_roots = [
        child
        for child in children
        if child.get("vdev_class") == group_name and child.get("node_kind") == "group"
    ]
    if group_roots:
        nodes: list[dict] = []
        for group_root in group_roots:
            group_children = group_root.get("children", []) or []
            nodes.extend(group_children or [group_root])
        return nodes

    return [child for child in children if child.get("vdev_class") == group_name]


def _build_topology_summary_item(
    node: dict,
    disk_lookup: dict[str, dict],
    available_devices: list[dict],
    *,
    scan_active: bool = False,
) -> dict:
    member_nodes = _flatten_leaf_member_nodes(node)
    members = []
    replace_target = str(node.get("name") or "-")
    member_devices: list[dict] = []
    for leaf in member_nodes:
        member_name = str(leaf.get("name") or "-")
        device = _lookup_topology_device(member_name, disk_lookup)
        if device:
            member_devices.append(device)
        member_state = str(leaf.get("state") or "").strip().upper() or None
        display_label = (device or {}).get("displayName") or (device or {}).get("diskPath") or (device or {}).get("path") or member_name
        replace_candidates = _build_replace_candidates(device, available_devices)
        can_replace = bool(replace_candidates)
        members.append(
            {
                "name": member_name,
                "path": (device or {}).get("kernelPath") or (device or {}).get("diskPath") or (device or {}).get("path") or member_name,
                "diskId": (device or {}).get("diskId") or member_name,
                "diskKey": (device or {}).get("diskKey") or None,
                "model": (device or {}).get("model") or None,
                "state": member_state,
                "read": leaf.get("read"),
                "write": leaf.get("write"),
                "cksum": leaf.get("cksum"),
                # For devices that are already inside a pool, maintenance
                # commands must use the exact member name reported by
                # `zpool status -L`. The UI still gets the friendly aliases and
                # canonical by-id path separately for display and matching.
                "commandTarget": member_name,
                "rawCommandTarget": member_name,
                # Replace is slightly different from offline/online on Linux:
                # pools that were created from whole disks may expose a child
                # partition as the leaf member while `zpool replace` still
                # expects the higher-level device node token. Keep a dedicated
                # replace target so the frontend does not reuse the wrong
                # command identity.
                "replaceTarget": replace_target if str(node.get("node_kind") or "") == "device" else member_name,
                "rawReplaceTarget": replace_target if str(node.get("node_kind") or "") == "device" else member_name,
                "preferredPath": (device or {}).get("commandPath") or member_name,
                "displayLabel": display_label,
                "kernelPath": (device or {}).get("kernelPath") or (device or {}).get("diskPath") or (device or {}).get("path") or member_name,
                "byIdPath": (device or {}).get("byIdPath") or None,
                "aliases": (device or {}).get("aliases") or [display_label],
                "canOffline": _can_offline_member(member_state),
                "canOnline": _can_online_member(member_state),
                "canReplace": can_replace,
                "replaceReason": None if can_replace else "No unused replacement disks are currently available.",
                # Attach candidate metadata directly to the leaf member so the
                # frontend can offer replace without recomputing qualification.
                "replaceCandidates": replace_candidates,
                "offlineReason": _offline_reason(member_state),
                "onlineReason": _online_reason(member_state),
            }
        )
    item_display_label = str(node.get("name") or "-")
    if node.get("node_kind") == "device" and members:
        item_display_label = str(members[0].get("displayLabel") or members[0].get("path") or item_display_label)
    raidz_expand_candidates = _build_raidz_expand_candidates(
        node=node,
        member_devices=member_devices,
        available_devices=available_devices,
        scan_active=scan_active,
    )
    can_raidz_expand = bool(raidz_expand_candidates)
    raidz_expand_reason = _raidz_expand_reason(
        node=node,
        member_devices=member_devices,
        available_devices=available_devices,
        scan_active=scan_active,
        candidates=raidz_expand_candidates,
    )
    smallest_member_size = _smallest_member_size(member_devices)
    return {
        "name": node.get("name"),
        "displayLabel": item_display_label,
        "vdevClass": node.get("vdev_class"),
        "roleLabel": node.get("role_label"),
        "nodeKind": node.get("node_kind"),
        "state": node.get("state"),
        "layout": _infer_layout(node),
        "commandTarget": replace_target if str(node.get("node_kind") or "") == "device" else node.get("name"),
        "rawCommandTarget": node.get("name"),
        # RAID-Z expansion operates on the vdev token itself instead of any
        # individual leaf member, so the UI needs item-level candidates.
        "canRaidzExpand": can_raidz_expand,
        "raidzExpandReason": raidz_expand_reason,
        "raidzExpandCandidates": raidz_expand_candidates,
        "raidzWidth": len(member_nodes),
        "smallestMemberSize": smallest_member_size,
        "members": members,
    }


def _build_removal_target(node: dict, disk_lookup: dict[str, dict]) -> dict:
    summary_item = _build_topology_summary_item(node, disk_lookup, [])
    display_label = summary_item.get("displayLabel") or summary_item["name"]
    command_target = node.get("name")
    raw_command_target = node.get("name")
    if summary_item.get("nodeKind") == "device" and summary_item.get("members"):
        member = summary_item["members"][0]
        display_label = member.get("displayLabel") or member.get("path") or display_label
        command_target = member.get("rawCommandTarget") or member.get("commandTarget") or command_target
    return {
        **summary_item,
        "commandTarget": command_target,
        "rawCommandTarget": raw_command_target,
        "displayLabel": display_label,
        "targetType": "vdev" if summary_item.get("nodeKind") == "vdev" else "device",
    }


def _flatten_leaf_member_nodes(node: dict) -> list[dict]:
    children = node.get("children", []) or []
    if not children:
        return [node]
    names: list[dict] = []
    for child in children:
        names.extend(_flatten_leaf_member_nodes(child))
    return names


def _infer_layout(node: dict) -> str:
    if node.get("layout"):
        return _normalize_layout_name(str(node["layout"]))
    name = str(node.get("name") or "")
    if name.startswith("mirror"):
        return "mirror"
    if name.startswith("raidz"):
        return _normalize_layout_name(name.split("-", 1)[0])
    return "stripe"


def _normalize_layout_name(layout: str) -> str:
    normalized = str(layout or "").strip().lower()
    # Some hosts label single-parity RAID-Z as `raidz1`, but the rest of the
    # UI and capability checks already treat that as plain `raidz`.
    if normalized == "raidz1":
        return "raidz"
    return normalized


def _topology_group_label(group_name: str) -> str:
    return {
        "data": "Data VDEVs",
        "log": "Log / ZIL",
        "cache": "Cache / L2ARC",
        "special": "Special",
        "dedup": "Dedup",
        "spare": "Spare",
    }[group_name]


def _build_available_topology_devices(disks: list[dict]) -> list[dict]:
    candidates: list[dict] = []
    for disk in disks:
        if not _disk_is_available_for_topology(disk):
            continue
        candidates.append(
            {
                "name": disk.get("name"),
                "path": disk.get("path"),
                "diskId": disk.get("diskId"),
                "diskKey": disk.get("diskKey"),
                "displayName": disk.get("displayName") or disk.get("path"),
                "kernelPath": disk.get("kernelPath") or disk.get("path"),
                "byIdPath": disk.get("byIdPath"),
                "commandPath": disk.get("commandPath") or disk.get("path"),
                "model": disk.get("model"),
                "size": disk.get("size"),
                "filesystem": disk.get("filesystem"),
                "supportedVdevClasses": ["log", "cache", "special", "dedup", "spare"],
            }
        )
    return candidates


def _build_replace_candidates(device: dict | None, available_devices: list[dict]) -> list[dict]:
    current_disk_key = str((device or {}).get("diskKey") or "").strip()
    current_kernel_path = str((device or {}).get("kernelPath") or (device or {}).get("diskPath") or "").strip()
    current_by_id_path = str((device or {}).get("byIdPath") or "").strip()
    candidates: list[dict] = []
    for candidate in available_devices:
        if current_disk_key and str(candidate.get("diskKey") or "").strip() == current_disk_key:
            continue
        if current_kernel_path and str(candidate.get("kernelPath") or "").strip() == current_kernel_path:
            continue
        if current_by_id_path and str(candidate.get("byIdPath") or "").strip() == current_by_id_path:
            continue
        candidates.append(candidate)
    return candidates


def _build_raidz_expand_candidates(
    *,
    node: dict,
    member_devices: list[dict],
    available_devices: list[dict],
    scan_active: bool,
) -> list[dict]:
    if str(node.get("node_kind") or "") != "vdev":
        return []
    if str(node.get("vdev_class") or "") != "data":
        return []
    if _infer_layout(node) not in {"raidz", "raidz2", "raidz3"}:
        return []
    if scan_active:
        return []

    # Let the operator open the expansion dialog even when the current member
    # size cannot be derived from lsblk with certainty. We still validate at
    # submit time when enough information is available, and otherwise let ZFS
    # return the authoritative error.
    return list(available_devices)


def _raidz_expand_reason(
    *,
    node: dict,
    member_devices: list[dict],
    available_devices: list[dict],
    scan_active: bool,
    candidates: list[dict],
) -> str | None:
    if str(node.get("node_kind") or "") != "vdev":
        return "RAID-Z expansion is only available on vdev items."
    if str(node.get("vdev_class") or "") != "data":
        return "RAID-Z expansion is only offered for data vdevs."
    layout = _infer_layout(node)
    if layout not in {"raidz", "raidz2", "raidz3"}:
        return "This vdev is not a RAID-Z layout."
    if scan_active:
        return "Another pool scan task is already running, so RAID-Z expansion is temporarily blocked."
    if not available_devices:
        return "No unused disks are currently available for RAID-Z expansion."
    if candidates:
        return None
    return "No unused disk is currently available for RAID-Z expansion."


def _smallest_member_size(member_devices: list[dict]) -> int | None:
    sizes = [
        size
        for size in (
            _coerce_size_bytes(device.get("size")) or _coerce_size_bytes(device.get("parentSize"))
            for device in member_devices
        )
        if size is not None and size > 0
    ]
    if not sizes:
        return None
    return min(sizes)


def _coerce_size_bytes(value) -> int | None:
    if value in (None, "", "-"):
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _disk_is_available_for_topology(disk: dict) -> bool:
    if disk.get("poolName") and disk.get("poolName") != "-":
        return False
    filesystem = str(disk.get("filesystem") or "-").lower()
    if not _is_reusable_filesystem(filesystem, disk.get("poolName")):
        return False
    for partition in disk.get("partitions", []):
        partition_pool = partition.get("poolName")
        partition_filesystem = str(partition.get("filesystem") or "-").lower()
        if partition_pool and partition_pool != "-":
            return False
        if not _is_reusable_filesystem(partition_filesystem, partition_pool):
            return False
    return True


def _can_offline_member(state: str | None) -> bool:
    normalized = str(state or "").upper()
    return normalized in {"ONLINE", "DEGRADED"}


def _can_online_member(state: str | None) -> bool:
    normalized = str(state or "").upper()
    return normalized == "OFFLINE"




def _offline_reason(state: str | None) -> str | None:
    normalized = str(state or "").upper()
    if _can_offline_member(normalized):
        return None
    if normalized == "OFFLINE":
        return "This device is already offline."
    if not normalized:
        return "The device state is unknown, so offline is not offered."
    return f"Offline is not offered for device state {normalized}."


def _online_reason(state: str | None) -> str | None:
    normalized = str(state or "").upper()
    if _can_online_member(normalized):
        return None
    if not normalized:
        return "The device state is unknown, so online is not offered."
    return f"Online is only offered when the device is OFFLINE, but the current state is {normalized}."


def _is_reusable_filesystem(filesystem: str | None, pool_name: str | None) -> bool:
    normalized_fs = str(filesystem or "-").lower()
    normalized_pool = str(pool_name or "-")
    if normalized_fs in {"-", "", "none", "unknown"}:
        return True
    # Keep stale ZFS labels visible in the disks table, but allow the disk to
    # be reused once it no longer belongs to any active pool.
    if normalized_fs == "zfs_member" and normalized_pool == "-":
        return True
    return False


def _annotate_topology_status(status: dict) -> dict:
    if not status:
        return {}

    config = status.get("config", []) or []
    if not config:
        return status

    pool_name = str(status.get("pool") or config[0].get("name") or "")
    return {
        **status,
        "config": [_annotate_topology_node(node, pool_name=pool_name, current_class="data", parent_kind="pool") for node in config],
    }


def _annotate_topology_node(
    node: dict,
    *,
    pool_name: str,
    current_class: str,
    parent_kind: str,
) -> dict:
    name = str(node.get("name") or "")
    node_kind = _topology_node_kind(name, pool_name, has_children=bool(node.get("children")))
    next_class = _topology_vdev_class(name, pool_name, current_class=current_class, parent_kind=parent_kind)
    layout = _infer_layout({"name": name})
    role_label = _topology_group_label(next_class) if next_class in {"data", "log", "cache", "special", "dedup", "spare"} else None

    return {
        **node,
        "display_name": name,
        "vdev_class": next_class,
        "role_label": role_label,
        "node_kind": node_kind,
        "layout": layout if node_kind == "vdev" else None,
        "children": [
            _annotate_topology_node(
                child,
                pool_name=pool_name,
                current_class=next_class,
                parent_kind=node_kind,
            )
            for child in (node.get("children") or [])
        ],
    }


def _topology_node_kind(name: str, pool_name: str, *, has_children: bool) -> str:
    lowered = name.lower()
    if name == pool_name:
        return "pool"
    if lowered in {"logs", "cache", "special", "dedup", "spares"}:
        return "group"
    if has_children or lowered.startswith("mirror") or lowered.startswith("raidz"):
        return "vdev"
    return "device"


def _topology_vdev_class(name: str, pool_name: str, *, current_class: str, parent_kind: str) -> str:
    lowered = name.lower()
    if name == pool_name:
        return "pool"
    if lowered == "logs":
        return "log"
    if lowered == "cache":
        return "cache"
    if lowered == "special":
        return "special"
    if lowered == "dedup":
        return "dedup"
    if lowered == "spares":
        return "spare"
    if parent_kind == "pool":
        return "data"
    return current_class
