from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.snapshot import SnapshotDestroyResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zfs_snapshot_destroy_command(snapshot: str, *, recursive: bool = False) -> str:
    parts = ["zfs", "destroy"]
    if recursive:
        parts.append("-r")
    parts.append(quote(snapshot))
    return " ".join(parts)


@dataclass(slots=True)
class SnapshotDestroyer:
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

    async def destroy_snapshot(self, snapshot: str, *, recursive: bool = False) -> SnapshotDestroyResponse:
        command = build_zfs_snapshot_destroy_command(snapshot, recursive=recursive)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return SnapshotDestroyResponse(
                snapshot=snapshot,
                success=success,
                message="Snapshot destroyed successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return SnapshotDestroyResponse(
                snapshot=snapshot,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the snapshot destroy command."
