# tests

> [中文版本](./README.zh-CN.md)

Backend test directory.

## Current Coverage

- `test_api.py`: `GET /api/state` snapshot shape and `/docs` availability
- `test_ws.py`: Initial WebSocket push and state updates
- `test_config.py`: Configuration model and example JSON validity
- `test_parser.py`: `lsblk`, `blkid`, `zpool status/list`, dataset list, property, and JSON-fixture parsing
- `test_ssh_client.py`: Reconnection after a stale SSH connection

## Current Test Focus

- `AppState(meta, data)` structure
- `summary / disks / pools / datasets` new structure
- `AppState` summary, disk, pool, and dataset data structures
- Single-pool, multi-pool, and empty-result parsing boundaries
- Loading the example configuration through the current Pydantic model

## Not Yet Covered

- Pool, dataset, and snapshot write endpoints or task lifecycles
- Schedule execution, recovery, and retention policies
- ATA/NVMe SMART JSON parsing, polling, or endpoints

`fixtures/smart_info_sample.txt` is currently a parser/debugging sample; fixture mode does not automatically inject it into SMART poll results.
