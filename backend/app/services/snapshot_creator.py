from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.snapshot import SnapshotCreateRequest, SnapshotCreateResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zfs_snapshot_command(*, dataset: str, payload: SnapshotCreateRequest) -> str:
    parts = ["zfs", "snapshot"]
    if payload.recursive:
        parts.append("-r")
    for property_name, property_value in sorted((payload.properties or {}).items()):
        parts.extend(["-o", quote(f"{property_name}={property_value}")])
    parts.append(quote(f"{dataset}@{payload.name}"))
    return " ".join(parts)


@dataclass(slots=True)
class SnapshotCreator:
    config: AppConfig
    _ssh_client: SSHClient = field(init=False)

    def __post_init__(self) -> None:
        self._ssh_client = SSHClient(
            SSHConfig(
                host=self.config.ssh.host,
                username=self.config.ssh.username,
                port=self.config.ssh.port,
                password=self.config.ssh.password,
                known_hosts=self.config.ssh.known_hosts,
                client_keys=self.config.ssh.key_files,
                connect_timeout=self.config.ssh.connect_timeout,
                keepalive_interval=self.config.ssh.keepalive_interval,
                keepalive_count_max=self.config.ssh.keepalive_count_max,
            )
        )

    async def close(self) -> None:
        await self._ssh_client.close()

    async def create_snapshot(self, dataset: str, payload: SnapshotCreateRequest) -> SnapshotCreateResponse:
        full_name = f"{dataset}@{payload.name}"
        command = build_zfs_snapshot_command(dataset=dataset, payload=payload)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return SnapshotCreateResponse(
                snapshot=full_name,
                success=success,
                message="Snapshot created successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return SnapshotCreateResponse(
                snapshot=full_name,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the snapshot creation command."
