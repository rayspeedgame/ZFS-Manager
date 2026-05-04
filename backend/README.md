# Backend

> [中文版本](./README.zh-CN.md)

The backend is responsible for three things: collecting remote host state, normalizing raw command output into unified snapshots, and executing ZFS/ZPool write operations with forced state refresh afterward.

## Main Responsibilities

- Execute read-only commands via SSH to collect:
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status/list/get`
  - `zfs list/get`
- Parse raw output into unified `meta + data` snapshots
- Expose REST endpoints:
  - State read and forced refresh
  - Settings read, save, and SSH test
  - Login status, login, and logout
  - Pool and dataset write operations
- Push latest snapshots via WebSocket

## Directory Structure

- `app/api/`: REST and WebSocket entry points
- `app/core/`: Configuration, auth, shared state, and other infrastructure
- `app/schemas/`: Pydantic request, response, and snapshot models
- `app/services/`: Polling, state aggregation, and write operation execution
- `app/ssh/`: SSH client, command definitions, and parsers
- `config/`: Current active configuration directory
- `tests/fixtures/`: Fixture mode input samples

## Current Implementation Focus

- `StatePoller` refreshes at different frequencies for `pools / datasets / disks / properties`
- Write operations uniformly call `poller.refresh_once(force_all=True)` upon completion
- Settings save hot-reloads the runtime instead of requiring manual backend restart
- Auth is lightweight cookie-based login, disabled by default, can be enabled via settings page

## Startup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
