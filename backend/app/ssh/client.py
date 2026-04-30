from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import asyncssh


@dataclass(slots=True)
class SSHConfig:
    host: str
    username: str
    port: int = 22
    password: str | None = None
    known_hosts: str | Path | None = None
    client_keys: list[str | Path] | None = None
    connect_timeout: float = 10.0
    keepalive_interval: float = 30.0
    keepalive_count_max: int = 3


class SSHClient:
    """Small asyncssh wrapper for phase 1 command execution."""

    def __init__(self, config: SSHConfig) -> None:
        self._config = config
        self._connection: Any | None = None
        # Guard connection creation/teardown so concurrent callers reuse the
        # same SSH session instead of racing to open multiple ones.
        self._lock = asyncio.Lock()

    async def connect(self) -> Any:
        import asyncssh

        if self._has_live_connection():
            return self._connection

        async with self._lock:
            if self._has_live_connection():
                return self._connection

            self._connection = None

            # Delay importing asyncssh until connect-time so offline parser
            # development can still run without the package being installed.
            self._connection = await asyncssh.connect(
                host=self._config.host,
                port=self._config.port,
                username=self._config.username,
                password=self._config.password,
                known_hosts=self._config.known_hosts,
                client_keys=self._normalize_paths(self._config.client_keys),
                login_timeout=self._config.connect_timeout,
                keepalive_interval=self._config.keepalive_interval,
                keepalive_count_max=self._config.keepalive_count_max,
            )
            return self._connection

    async def run(self, command: str, *, check: bool = True, timeout: float | None = None) -> str:
        connection = await self.connect()
        try:
            result = await asyncio.wait_for(connection.run(command, check=check), timeout=timeout)
            return result.stdout
        except Exception as exc:
            if not self._should_retry_after_disconnect(exc):
                raise

            # Rebuild the SSH session once if the remote side closed it.
            await self._drop_connection()
            connection = await self.connect()
            result = await asyncio.wait_for(connection.run(command, check=check), timeout=timeout)
            return result.stdout

    async def close(self) -> None:
        async with self._lock:
            if self._connection is not None:
                self._connection.close()
                await self._connection.wait_closed()
                self._connection = None

    def _has_live_connection(self) -> bool:
        if self._connection is None:
            return False

        is_closing = getattr(self._connection, "is_closing", None)
        if callable(is_closing):
            return not is_closing()
        return True

    async def _drop_connection(self) -> None:
        async with self._lock:
            if self._connection is None:
                return

            self._connection.close()
            await self._connection.wait_closed()
            self._connection = None

    @staticmethod
    def _should_retry_after_disconnect(exc: Exception) -> bool:
        message = str(exc).lower()
        return (
            "connection closed" in message
            or "connection lost" in message
            or "broken pipe" in message
            or isinstance(exc, (BrokenPipeError, ConnectionAbortedError, ConnectionResetError))
        )

    async def __aenter__(self) -> "SSHClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    @staticmethod
    def _normalize_paths(paths: list[str | Path] | None) -> list[str] | None:
        if not paths:
            return None
        return [str(Path(path).expanduser()) for path in paths]
