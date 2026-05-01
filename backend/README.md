# Backend

This backend provides the host-integration and realtime API layer for
ZFS-Manager.

It currently includes:

- SSH-based host querying
- structured parsers for disk, pool, and dataset state
- an in-memory snapshot store
- retained last-good data when live refresh fails
- decoupled polling schedules by resource category
- FastAPI REST endpoints
- FastAPI WebSocket streaming
- fixture mode for local development
- live SSH mode for real host polling

## Folder Map

```text
backend/
|- app/                # backend application package
|- scripts/            # local debugging helpers
|- tests/              # tests and parser fixtures
|- config.example.json # example runtime config
|- config.json         # local private runtime config (ignored)
`- requirements.txt
```

See:

- [app/README.md](./app/README.md)
- [scripts/README.md](./scripts/README.md)
- [tests/README.md](./tests/README.md)

## Runtime Modes

### Fixture mode

Uses saved sample output files instead of a live SSH target.

Best for:

- parser work
- API and frontend integration
- local development without a host
- validating the decoupled polling logic without SSH

### SSH mode

Uses the configured host and credentials to fetch live state.

Best for:

- real integration testing
- staging
- deployment

## Polling Model

The poller no longer refreshes every resource at the same rate.

Current schedule categories:

- `disks`
- `pools`
- `datasets`
- `properties`

The backend keeps separate caches for these sections, merges them into one
snapshot, and exposes refresh metadata in `meta.refresh_plan_seconds`.

## Configuration

Create `backend/config.json` from [config.example.json](./config.example.json).

Important settings:

- `poller.mode`
- `poller.interval_seconds`
- `poller.tick_seconds`
- `poller.fallback_to_fixture`
- `poller.pools_interval_seconds`
- `poller.datasets_interval_seconds`
- `poller.disks_interval_seconds`
- `poller.properties_interval_seconds`
- `ssh.host`
- `ssh.username`
- `ssh.password`
- `ssh.key_files`
- `ssh.command_timeout`
- `ssh.keepalive_interval`
- `ssh.keepalive_count_max`

Environment-variable overrides are also supported:

- `ZFS_MANAGER_POLLER_MODE`
- `ZFS_MANAGER_POLLER_INTERVAL`
- `ZFS_MANAGER_POLLER_TICK`
- `ZFS_MANAGER_POLLER_FALLBACK`
- `ZFS_MANAGER_POLLER_POOLS_INTERVAL`
- `ZFS_MANAGER_POLLER_DATASETS_INTERVAL`
- `ZFS_MANAGER_POLLER_DISKS_INTERVAL`
- `ZFS_MANAGER_POLLER_PROPERTIES_INTERVAL`
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

## Run the API

```bash
uvicorn app.main:app --reload
```

Useful endpoints:

- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- REST state: [http://127.0.0.1:8000/api/state](http://127.0.0.1:8000/api/state)
- Health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- WebSocket: `ws://127.0.0.1:8000/ws/state`

## Parser Debugging

Run directly against saved samples:

```bash
python scripts/debug_ssh_parser.py --source file --command disk_overview --input-file tests/fixtures/disk_overview_sample.txt
python scripts/debug_ssh_parser.py --source file --command zpool_overview --input-file tests/fixtures/zpool_overview_sample.txt
python scripts/debug_ssh_parser.py --source file --command dataset_overview --input-file tests/fixtures/dataset_overview_sample.txt
```

Run against a real host:

```bash
python scripts/debug_ssh_parser.py --source ssh --command disk_overview --host 192.168.1.10 --username root --key-file ~/.ssh/id_ed25519
```

## Tests

```bash
pytest
```

The suite covers:

- config loading
- parser output
- REST endpoints
- WebSocket streaming
- SSH reconnect behavior
- snapshot fields added for domain rows and refresh metadata
