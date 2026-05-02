from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.pool_create import PoolCreateRequest, PoolCreateResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_create_command(payload: PoolCreateRequest) -> str:
    parts = ["zpool", "create"]

    for prop in payload.properties:
        parts.extend(["-o", quote(f"{prop.name}={prop.value}")])

    parts.append(quote(payload.name))

    data_vdevs = [vdev for vdev in payload.vdevs if vdev.category == "data"]
    aux_vdevs = [vdev for vdev in payload.vdevs if vdev.category != "data"]

    for vdev in data_vdevs:
        parts.extend(_serialize_vdev(vdev))

    for category in ("log", "cache", "special", "dedup", "spare"):
        category_vdevs = [vdev for vdev in aux_vdevs if vdev.category == category]
        if not category_vdevs:
            continue
        parts.append(category)
        for vdev in category_vdevs:
            parts.extend(_serialize_vdev(vdev))

    return " ".join(parts)


def _serialize_vdev(vdev) -> list[str]:
    parts: list[str] = []
    if vdev.layout != "stripe":
        parts.append(vdev.layout)
    parts.extend(quote(device) for device in vdev.devices)
    return parts


@dataclass(slots=True)
class PoolCreator:
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

    async def create_pool(self, payload: PoolCreateRequest) -> PoolCreateResponse:
        command = build_zpool_create_command(payload)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return PoolCreateResponse(
                pool=payload.name,
                success=success,
                message="Pool created successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return PoolCreateResponse(
                pool=payload.name,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the pool creation command."
