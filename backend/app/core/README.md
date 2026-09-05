# core

> [中文版本](./README.zh-CN.md)

This layer contains backend infrastructure code.

## File Descriptions

- `config.py`: Configuration read, save, path resolution, and environment variable overrides
- `auth.py`: Login toggle check, cookie read/write, and authentication check
- `client_tracker.py`: Tracks WebSocket client count for active versus idle polling intervals
- `state.py`: Saves current application snapshot for REST and WebSocket sharing

## Configuration Focus

- Default configuration directory is `backend/config/`
- Still compatible with legacy `backend/config.json` as fallback path
- Also supports `ZFS_MANAGER_CONFIG` to specify custom config file

Main configuration blocks:

- `poller` (including `smart_interval_seconds` / `idle_smart_interval_seconds`)
- `ssh`
- `auth`
- `disk_labels`

These configurations allow separating high-frequency state and low-frequency property refresh, and also allow directly adjusting connection and login behavior through the settings page.

Task records default to a SQLite database in the configuration directory; `ZFS_MANAGER_TASK_DB` can select a separate path.
