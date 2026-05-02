from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
        self._interval_seconds = config.poller.interval_seconds
        self._tick_seconds = max(1, config.poller.tick_seconds)
        self._task: asyncio.Task[None] | None = None
        self._backend_root = Path(__file__).resolve().parents[2]
        self._fixtures_dir = self._backend_root / "tests" / "fixtures"
        self._ssh_client = self._build_ssh_client() if config.poller.mode == "ssh" else None
        self._disk_cache = CachedPayload()
        self._zpool_core_cache = CachedPayload()
        self._zpool_properties_cache = CachedPayload()
        self._dataset_core_cache = CachedPayload()
        self._dataset_properties_cache = CachedPayload()
        self._schedules = {
            "disks": ScheduledRefresh(max(1, config.poller.disks_interval_seconds)),
            "pools": ScheduledRefresh(max(1, config.poller.pools_interval_seconds)),
            "datasets": ScheduledRefresh(max(1, config.poller.datasets_interval_seconds)),
            "properties": ScheduledRefresh(max(1, config.poller.properties_interval_seconds)),
        }

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
            await asyncio.sleep(self._tick_seconds)

    async def refresh_once(self) -> AppState:
        attempt_at = datetime.now(timezone.utc)
        due_jobs = self._collect_due_jobs(attempt_at)

        if not due_jobs and self._has_cached_data():
            return await state_store.get_state()

        if not due_jobs:
            due_jobs = list(self._schedules.keys())

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

        return AppState(
            meta=AppMeta(
                app_status=app_status,
                source_status=source_status,
                message=message,
                refresh_interval_seconds=self._interval_seconds,
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
                disks=_build_disk_rows(disk_data, dataset_data, zpool_data),
                pools=_build_pool_rows(zpool_data),
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


def _build_disk_rows(disk_data: dict, dataset_data: dict, zpool_data: dict) -> list[dict]:
    devices = disk_data.get("lsblk", {}).get("blockdevices", [])
    blkid_rows = disk_data.get("blkid", [])
    datasets = dataset_data.get("datasets", [])
    zpool_roots = {
        str(dataset.get("name")).split("/")[0]
        for dataset in datasets
        if dataset.get("name")
    }
    pool_membership: dict[str, str] = {}

    for dataset in datasets:
        mountpoint = dataset.get("mountpoint")
        name = dataset.get("name")
        if mountpoint and name:
            pool_membership[mountpoint] = str(name).split("/")[0]

    topology_membership = _build_topology_membership_map(zpool_data)
    single_pool_name = next(iter(zpool_roots), None) if len(zpool_roots) == 1 else None

    rows: list[dict] = []
    for device in devices:
        children = device.get("children") or []
        partitions = [
            _build_partition_row(
                child,
                blkid_rows,
                topology_membership,
                single_pool_name,
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
            single_pool_name=single_pool_name,
        )
        filesystem = primary_filesystem or _filesystem_from_device(
            device=device,
            blkid_rows=blkid_rows,
        )

        rows.append(
            {
                **device,
                "filesystem": filesystem or "-",
                "poolName": device_pool_name or primary_pool_name or single_pool_name or "-",
                "partitionPath": primary_partition.get("path") or "-",
                "partitions": partitions,
            }
        )

    return rows


def _build_pool_rows(zpool_data: dict) -> list[dict]:
    pools = zpool_data.get("pools", [])
    properties = zpool_data.get("properties", {})
    status_by_pool = zpool_data.get("status_by_pool", {})
    rows: list[dict] = []

    for pool in pools:
        name = pool.get("name")
        rows.append(
            {
                **pool,
                "status": status_by_pool.get(name),
                "properties": properties.get(name, {}),
            }
        )

    return rows


def _build_dataset_rows(dataset_data: dict) -> list[dict]:
    datasets = dataset_data.get("datasets", [])
    properties = dataset_data.get("properties", {})
    rows: list[dict] = []

    for dataset in datasets:
        name = str(dataset.get("name") or "")
        dataset_properties = properties.get(name, {})
        rows.append(
            {
                **dataset,
                "depth": max(0, len(name.split("/")) - 1) if name else 0,
                "poolName": name.split("/")[0] if name else "-",
                "shortName": name.split("/")[-1] if name else "-",
                "properties": dataset_properties,
                "sourceSummary": _get_property_source_summary(dataset_properties),
            }
        )

    return rows


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
    blkid_rows: list[dict],
    topology_membership: dict[str, str],
    single_pool_name: str | None,
) -> dict:
    partition_path = partition.get("path")
    blkid = next((item for item in blkid_rows if item.get("device") == partition_path), None)
    filesystem = (blkid or {}).get("type") or "-"
    pool_name = _lookup_pool_name(partition_path, partition.get("name"), topology_membership)
    if not pool_name and single_pool_name and filesystem == "zfs_member":
        pool_name = single_pool_name

    return {
        **partition,
        "filesystem": filesystem,
        "poolName": pool_name or "-",
    }


def _build_topology_membership_map(zpool_data: dict) -> dict[str, str]:
    membership: dict[str, str] = {}
    status_by_pool = zpool_data.get("status_by_pool", {})

    def visit(node: dict, pool_name: str) -> None:
        name = node.get("name")
        if name:
            for candidate in _device_identity_candidates(name, name):
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
    single_pool_name: str | None,
) -> str | None:
    device_pool_name = _lookup_pool_name(device.get("path"), device.get("name"), topology_membership)
    if device_pool_name:
        return device_pool_name
    if primary_partition.get("poolName") and primary_partition.get("poolName") != "-":
        return str(primary_partition["poolName"])
    if single_pool_name and (
        primary_partition.get("filesystem") == "zfs_member" or device.get("type") == "disk"
    ):
        return single_pool_name
    return None


def _filesystem_from_device(*, device: dict, blkid_rows: list[dict]) -> str:
    device_path = device.get("path")
    blkid = next((item for item in blkid_rows if item.get("device") == device_path), None)
    return (blkid or {}).get("type") or "-"


def _lookup_pool_name(path: str | None, name: str | None, topology_membership: dict[str, str]) -> str | None:
    for candidate in _device_identity_candidates(path, name):
        if candidate in topology_membership:
            return topology_membership[candidate]
    return None


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
