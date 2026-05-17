from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.pool_scrub import PoolScrubResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_scrub_command(pool: str, *, stop: bool = False) -> str:
    parts = ["zpool", "scrub"]
    if stop:
        parts.append("-s")
    parts.append(quote(pool))
    return " ".join(parts)


@dataclass(slots=True)
class PoolScrubber:
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

    async def start_scrub(self, pool: str) -> PoolScrubResponse:
        return await self._run(pool, action="start", stop=False)

    async def stop_scrub(self, pool: str) -> PoolScrubResponse:
        return await self._run(pool, action="stop", stop=True)

    async def _run(self, pool: str, *, action: str, stop: bool) -> PoolScrubResponse:
        command = build_zpool_scrub_command(pool, stop=stop)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolScrubResponse(
                pool=pool,
                action=action,
                success=success,
                message=(
                    f"Scrub {action} command completed successfully."
                    if success
                    else _build_failure_message(result.stderr, action)
                ),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolScrubResponse(
                pool=pool,
                action=action,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str, action: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return f"The remote host rejected the scrub {action} command."
