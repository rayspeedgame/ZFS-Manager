from __future__ import annotations

import asyncio
import sys
import types

from app.ssh.client import SSHClient, SSHConfig


class _FakeResult:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout
        self.stderr = ""
        self.exit_status = 0


class _FakeConnection:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self._closed = False

    async def run(self, command: str, check: bool = True) -> _FakeResult:
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return _FakeResult(str(response))

    def close(self) -> None:
        self._closed = True

    async def wait_closed(self) -> None:
        return None

    def is_closing(self) -> bool:
        return self._closed


def test_ssh_client_reconnects_after_closed_connection(monkeypatch) -> None:
    connections = [
        _FakeConnection([RuntimeError("SSH connection closed")]),
        _FakeConnection(["ok-after-reconnect"]),
    ]

    async def fake_connect(**kwargs):
        return connections.pop(0)

    fake_asyncssh = types.SimpleNamespace(connect=fake_connect)
    monkeypatch.setitem(sys.modules, "asyncssh", fake_asyncssh)

    client = SSHClient(SSHConfig(host="127.0.0.1", username="root"))
    result = asyncio.run(client.run("echo test"))

    assert result == "ok-after-reconnect"
