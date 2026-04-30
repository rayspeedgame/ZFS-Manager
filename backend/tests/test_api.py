from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_get_state_returns_snapshot() -> None:
    with TestClient(app) as client:
        response = client.get("/api/state")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["disk_overview"]["lsblk"]["blockdevices"][0]["name"] == "sda"
    assert body["zpool_overview"]["status"]["pool"] == "tank"
    assert body["dataset_overview"]["datasets"][1]["name"] == "tank/media"


def test_docs_endpoint_is_available() -> None:
    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
