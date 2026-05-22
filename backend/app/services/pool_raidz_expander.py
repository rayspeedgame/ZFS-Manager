from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.pool_raidz_expand import PoolRaidzExpandResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_raidz_expand_command(*, pool: str, vdev_target: str, new_device_target: str) -> str:
    return f"zpool attach {quote(pool)} {quote(vdev_target)} {quote(new_device_target)}"


@dataclass(slots=True)
class PoolRaidzExpander:
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

    async def expand_raidz(
        self,
        *,
        pool: str,
        vdev_target: str,
        new_device_target: str,
        vdev_label: str,
        new_device_label: str,
    ) -> PoolRaidzExpandResponse:
        command = build_zpool_raidz_expand_command(
            pool=pool,
            vdev_target=vdev_target,
            new_device_target=new_device_target,
        )
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolRaidzExpandResponse(
                pool=pool,
                success=success,
                message="RAID-Z expansion command submitted successfully." if success else _build_failure_message(result.stderr),
                vdev_target=vdev_target,
                new_device_target=new_device_target,
                vdev_label=vdev_label,
                new_device_label=new_device_label,
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolRaidzExpandResponse(
                pool=pool,
                success=False,
                message=str(exc),
                vdev_target=vdev_target,
                new_device_target=new_device_target,
                vdev_label=vdev_label,
                new_device_label=new_device_label,
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the RAID-Z expansion request."
