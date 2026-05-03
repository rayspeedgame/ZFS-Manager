from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.dataset_property_update import (
    DatasetPropertyUpdateItem,
    DatasetPropertyUpdateResult,
)
from app.ssh.client import SSHClient, SSHConfig


def build_zfs_set_command(*, dataset: str, property_name: str, value: str) -> str:
    assignment = f"{property_name}={value}"
    return f"zfs set {quote(assignment)} {quote(dataset)}"


@dataclass(slots=True)
class DatasetPropertyUpdater:
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

    async def apply_dataset_changes(
        self,
        *,
        dataset: str,
        changes: list[DatasetPropertyUpdateItem],
    ) -> list[DatasetPropertyUpdateResult]:
        results: list[DatasetPropertyUpdateResult] = []

        for change in changes:
            command = build_zfs_set_command(
                dataset=dataset,
                property_name=change.property,
                value=change.value,
            )
            try:
                result = await self._ssh_client.run_detailed(
                    command,
                    check=False,
                    timeout=self.config.ssh.command_timeout,
                )
                success = result.success
                results.append(
                    DatasetPropertyUpdateResult(
                        property=change.property,
                        old_value=change.old_value,
                        new_value=change.value,
                        success=success,
                        message="Applied successfully." if success else _build_failure_message(result.stderr),
                        command=command,
                        exit_status=result.exit_status,
                        stdout=result.stdout.strip() or None,
                        stderr=result.stderr.strip() or None,
                    )
                )
            except Exception as exc:
                results.append(
                    DatasetPropertyUpdateResult(
                        property=change.property,
                        old_value=change.old_value,
                        new_value=change.value,
                        success=False,
                        message=str(exc),
                        command=command,
                        stderr=str(exc),
                    )
                )

        return results


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the dataset property update."
