from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.snapshot import SnapshotRollbackMode, SnapshotRollbackResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zfs_snapshot_rollback_command(snapshot: str, mode: SnapshotRollbackMode = "safe") -> str:
    parts = ["zfs", "rollback"]
    if mode == "prune_newer":
        parts.append("-r")
    elif mode == "force_dependents":
        parts.append("-R")
    parts.append(quote(snapshot))
    return " ".join(parts)


def derive_snapshot_dataset(snapshot: str) -> str:
    normalized = str(snapshot or "")
    if "@" not in normalized:
        return normalized
    return normalized.split("@", 1)[0]


@dataclass(slots=True)
class SnapshotRollbacker:
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

    async def rollback_snapshot(self, snapshot: str, mode: SnapshotRollbackMode = "safe") -> SnapshotRollbackResponse:
        dataset = derive_snapshot_dataset(snapshot)
        command = build_zfs_snapshot_rollback_command(snapshot, mode)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return SnapshotRollbackResponse(
                snapshot=snapshot,
                dataset=dataset,
                rollback_mode=mode,
                success=success,
                message="Snapshot rolled back successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return SnapshotRollbackResponse(
                snapshot=snapshot,
                dataset=dataset,
                rollback_mode=mode,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the snapshot rollback command."
