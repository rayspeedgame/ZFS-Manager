from __future__ import annotations

from dataclasses import dataclass, field
from shlex import quote

from app.core.config import AppConfig
from app.schemas.topology_update import PoolTopologyAddItem, PoolTopologyUpdateResult
from app.ssh.client import SSHClient, SSHConfig


def build_zpool_add_command(*, pool: str, addition: PoolTopologyAddItem) -> str:
    parts = ["zpool", "add", quote(pool)]
    category_token = _category_token(addition.category)
    layout_token = _layout_token(addition.layout)

    if category_token:
        parts.append(category_token)
    if layout_token:
        parts.append(layout_token)

    parts.extend(quote(device) for device in addition.devices)
    return " ".join(parts)


@dataclass(slots=True)
class PoolTopologyUpdater:
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

    async def apply_pool_additions(
        self,
        *,
        pool: str,
        additions: list[PoolTopologyAddItem],
    ) -> list[PoolTopologyUpdateResult]:
        results: list[PoolTopologyUpdateResult] = []

        for addition in additions:
            command = build_zpool_add_command(pool=pool, addition=addition)
            try:
                result = await self._ssh_client.run_detailed(
                    command,
                    check=False,
                    timeout=self.config.ssh.command_timeout,
                )
                success = result.success
                results.append(
                    PoolTopologyUpdateResult(
                        category=addition.category,
                        layout=addition.layout,
                        devices=addition.devices,
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
                    PoolTopologyUpdateResult(
                        category=addition.category,
                        layout=addition.layout,
                        devices=addition.devices,
                        success=False,
                        message=str(exc),
                        command=command,
                        stderr=str(exc),
                    )
                )

        return results


def _category_token(category: str) -> str:
    return {
        "data": "",
        "log": "log",
        "cache": "cache",
        "special": "special",
        "dedup": "dedup",
        "spare": "spare",
    }[category]


def _layout_token(layout: str) -> str:
    return "" if layout == "stripe" else layout


def _build_failure_message(stderr: str) -> str:
    cleaned = stderr.strip()
    if cleaned:
        return cleaned
    return "The remote host rejected the topology update."
