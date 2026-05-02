from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.pool_remove import PoolRemoveResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_remove_command(*, pool: str, command_target: str) -> str:
    return f"zpool remove {quote(pool)} {quote(command_target)}"


@dataclass(slots=True)
class PoolRemover:
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

    async def remove_target(
        self,
        *,
        pool: str,
        command_target: str,
        display_label: str,
        target_type: str,
        vdev_class: str,
        layout: str,
    ) -> PoolRemoveResponse:
        command = build_zpool_remove_command(pool=pool, command_target=command_target)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolRemoveResponse(
                pool=pool,
                command_target=command_target,
                display_label=display_label,
                target_type=target_type,
                vdev_class=vdev_class,
                layout=layout,
                success=success,
                message="Topology target removed successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolRemoveResponse(
                pool=pool,
                command_target=command_target,
                display_label=display_label,
                target_type=target_type,
                vdev_class=vdev_class,
                layout=layout,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the topology remove request."
