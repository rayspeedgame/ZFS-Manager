# Phase 1-3: SSH, Parser, FastAPI State Flow, and WebSocket

This backend starts with an SSH/parser slice and now includes a small FastAPI app backed by an in-memory state store.

## Configuration

Create `backend/config.json` based on [config.example.json](C:/Users/raysp/Documents/New%20project/backend/config.example.json).

- `poller.mode = "fixture"` keeps using saved sample outputs
- `poller.mode = "ssh"` switches the poller to the real host
- `poller.fallback_to_fixture = true` keeps the API available if SSH refresh fails

You can also override the same values with environment variables, which is useful in Docker:

- `ZFS_MANAGER_POLLER_MODE`
- `ZFS_MANAGER_POLLER_INTERVAL`
- `ZFS_MANAGER_POLLER_FALLBACK`
- `ZFS_MANAGER_SSH_HOST`
- `ZFS_MANAGER_SSH_USERNAME`
- `ZFS_MANAGER_SSH_PORT`
- `ZFS_MANAGER_SSH_PASSWORD`
- `ZFS_MANAGER_SSH_KEY_FILES`
- `ZFS_MANAGER_SSH_KNOWN_HOSTS`
- `ZFS_MANAGER_SSH_CONNECT_TIMEOUT`
- `ZFS_MANAGER_SSH_COMMAND_TIMEOUT`
- `ZFS_MANAGER_SSH_KEEPALIVE_INTERVAL`
- `ZFS_MANAGER_SSH_KEEPALIVE_COUNT_MAX`

## Install

```bash
pip install -r requirements.txt
```

## Run from saved sample

```bash
python scripts/debug_ssh_parser.py --source file --command lsblk --input-file tests/fixtures/lsblk_sample.json
python scripts/debug_ssh_parser.py --source file --command zpool --input-file tests/fixtures/zpool_status_sample.txt
python scripts/debug_ssh_parser.py --source file --command disk_overview --input-file tests/fixtures/disk_overview_sample.txt
python scripts/debug_ssh_parser.py --source file --command zpool_overview --input-file tests/fixtures/zpool_overview_sample.txt
python scripts/debug_ssh_parser.py --source file --command dataset_overview --input-file tests/fixtures/dataset_overview_sample.txt
```

## Run against a real host

```bash
python scripts/debug_ssh_parser.py --source ssh --command lsblk --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519 --save-output tests/fixtures/real_lsblk.json
python scripts/debug_ssh_parser.py --source ssh --command zpool --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519 --save-output tests/fixtures/real_zpool_status.txt
python scripts/debug_ssh_parser.py --source ssh --command disk_overview --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519 --save-output tests/fixtures/real_disk_overview.txt
python scripts/debug_ssh_parser.py --source ssh --command zpool_overview --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519 --save-output tests/fixtures/real_zpool_overview.txt
python scripts/debug_ssh_parser.py --source ssh --command dataset_overview --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519 --save-output tests/fixtures/real_dataset_overview.txt
```

## Recommended polling shape

- `disk_overview`: one round-trip for block devices, mounts, and blkid metadata
- `zpool_overview`: one round-trip for pool topology, capacity summary, and all pool properties
- `dataset_overview`: one round-trip for dataset list plus all dataset properties

## Test

```bash
pytest
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Then open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and call `GET /api/state`.

## WebSocket endpoint

- `ws://127.0.0.1:8000/ws/state`

The socket sends the latest state snapshot whenever the in-memory state store is updated.
