from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_state_websocket_streams_snapshot() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/ws/state") as websocket:
            payload = websocket.receive_json()

    assert payload["status"] in {"ready", "degraded"}
    assert payload["meta"]["refresh_plan_seconds"]["tick"] >= 1
    assert payload["data"]["disks"][0]["name"] == "sda"
    assert payload["disk_overview"]["lsblk"]["blockdevices"][0]["name"] == "sda"
