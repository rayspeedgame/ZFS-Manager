from __future__ import annotations

from pathlib import Path

from app.core.config import AppConfig


def test_app_config_accepts_ssh_mode() -> None:
    payload = {
        "poller": {"mode": "ssh", "interval_seconds": 5, "fallback_to_fixture": False},
        "ssh": {"host": "10.0.0.2", "username": "admin", "password": "secret"},
    }

    config = AppConfig.model_validate(payload)

    assert config.poller.mode == "ssh"
    assert config.poller.interval_seconds == 5
    assert config.ssh.host == "10.0.0.2"
    assert config.ssh.username == "admin"


def test_example_config_is_valid_json() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config.example.json"
    config = AppConfig.model_validate_json(config_path.read_text(encoding="utf-8"))

    assert config.poller.mode == "ssh"
    assert config.ssh.port == 22
