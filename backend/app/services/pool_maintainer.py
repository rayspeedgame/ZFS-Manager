from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.pool_maintenance import PoolMaintenanceActionResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_offline_command(*, pool: str, command_target: str) -> str:
    return f"zpool offline {quote(pool)} {quote(command_target)}"


def build_zpool_online_command(*, pool: str, command_target: str) -> str:
    return f"zpool online {quote(pool)} {quote(command_target)}"


def build_zpool_clear_command(*, pool: str) -> str:
    return f"zpool clear {quote(pool)}"


@dataclass(slots=True)
class PoolMaintainer:
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

    async def offline_device(self, *, pool: str, command_target: str, display_label: str) -> PoolMaintenanceActionResponse:
        return await self._run_device_action(
            action="offline",
            pool=pool,
            command_target=command_target,
            display_label=display_label,
            command=build_zpool_offline_command(pool=pool, command_target=command_target),
        )

    async def online_device(self, *, pool: str, command_target: str, display_label: str) -> PoolMaintenanceActionResponse:
        return await self._run_device_action(
            action="online",
            pool=pool,
            command_target=command_target,
            display_label=display_label,
            command=build_zpool_online_command(pool=pool, command_target=command_target),
        )

    async def clear_pool(self, *, pool: str) -> PoolMaintenanceActionResponse:
        command = build_zpool_clear_command(pool=pool)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolMaintenanceActionResponse(
                pool=pool,
                action="clear",
                success=success,
                message="Pool errors cleared successfully." if success else _build_failure_message(result.stderr, action="clear"),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolMaintenanceActionResponse(
                pool=pool,
                action="clear",
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )

    async def _run_device_action(
        self,
        *,
        action: str,
        pool: str,
        command_target: str,
        display_label: str,
        command: str,
    ) -> PoolMaintenanceActionResponse:
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolMaintenanceActionResponse(
                pool=pool,
                action=action,
                command_target=command_target,
                display_label=display_label,
                success=success,
                message=(
                    f"Pool device {action} completed successfully."
                    if success
                    else _build_failure_message(result.stderr, action=action)
                ),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolMaintenanceActionResponse(
                pool=pool,
                action=action,
                command_target=command_target,
                display_label=display_label,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str, *, action: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return f"The remote host rejected the pool {action} request."
