from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.dataset_create import DatasetCreateRequest, DatasetCreateResponse
from app.ssh.client import SSHClient, SSHConfig


def build_zfs_create_command(payload: DatasetCreateRequest) -> str:
    parts = ["zfs", "create"]
    properties = {property_item.name: property_item.value for property_item in payload.properties}

    if payload.type == "volume":
        volsize = properties.pop("volsize")
        for name, value in properties.items():
            parts.extend(["-o", quote(f"{name}={value}")])
        parts.extend(["-V", quote(volsize), quote(payload.full_name)])
        return " ".join(parts)

    for name, value in properties.items():
        parts.extend(["-o", quote(f"{name}={value}")])
    parts.append(quote(payload.full_name))
    return " ".join(parts)


@dataclass(slots=True)
class DatasetCreator:
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

    async def create_dataset(self, payload: DatasetCreateRequest) -> DatasetCreateResponse:
        command = build_zfs_create_command(payload)
        try:
            result = await self._ssh_client.run_detailed(
                command,
                check=False,
                timeout=self.config.ssh.command_timeout,
            )
            success = result.success
            return DatasetCreateResponse(
                dataset=payload.full_name,
                success=success,
                message="Dataset created successfully." if success else _build_failure_message(result.stderr),
                command=command,
                exit_status=result.exit_status,
                stdout=result.stdout.strip() or None,
                stderr=result.stderr.strip() or None,
            )
        except Exception as exc:
            return DatasetCreateResponse(
                dataset=payload.full_name,
                success=False,
                message=str(exc),
                command=command,
                stderr=str(exc),
            )


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the dataset creation command."
