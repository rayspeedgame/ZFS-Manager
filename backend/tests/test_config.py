from __future__ import annotations

from app.core.config import AppConfig, DEFAULT_EXAMPLE_CONFIG_PATH


def test_app_config_accepts_ssh_mode() -> None:
    payload = {
        "poller": {
            "mode": "ssh",
            "tick_seconds": 1,
            "pools_interval_seconds": 5,
            "fallback_to_fixture": False,
        },
        "ssh": {"host": "10.0.0.2", "username": "admin", "password": "secret"},
    }

    config = AppConfig.model_validate(payload)

    assert config.poller.mode == "ssh"
    assert config.poller.pools_interval_seconds == 5
    assert config.ssh.host == "10.0.0.2"
    assert config.ssh.username == "admin"


def test_example_config_is_valid_json() -> None:
    config_path = DEFAULT_EXAMPLE_CONFIG_PATH
    config = AppConfig.model_validate_json(config_path.read_text(encoding="utf-8"))

    assert config.poller.mode == "ssh"
    assert config.ssh.port == 22
