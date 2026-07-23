# tests

> [中文版本](./README.zh-CN.md)

Backend test directory.

## Current Coverage

- `test_api.py`: REST snapshot and write endpoints
- `test_ws.py`: WebSocket push
- `test_config.py`: Configuration read
- `test_parser.py`: Command parsing, including dataset / snapshot / multi-pool / SMART scenarios
- `test_ssh_client.py`: SSH client behavior

## Current Test Focus

- `AppState(meta, data)` structure
- `summary / disks / pools / datasets` new structure
- Pool / dataset write operation return result format
- `zfs list/get` parsing for snapshots
- SMART data parsing (ATA + NVMe) via `smart_info_sample.txt` fixture
