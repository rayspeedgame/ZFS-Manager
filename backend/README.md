# Backend

> [中文版本](./README.zh-CN.md)

The backend is responsible for four things: collecting remote host state, normalizing raw command output into unified snapshots, executing ZFS/ZPool write operations, and recording operator-visible tasks for those workflows.

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
  - Task list and task detail
- Push latest snapshots via WebSocket

## Directory Structure

- `app/api/`: REST and WebSocket entry points
- `app/core/`: Configuration, auth, shared state, and other infrastructure
- `app/schemas/`: Pydantic request, response, snapshot, and task models
- `app/services/`: Polling, state aggregation, write operation execution, and task registration
- `app/ssh/`: SSH client, command definitions, and parsers
- `config/`: Current active configuration directory
- `tests/fixtures/`: Fixture mode input samples

## Current Implementation Focus

- `StatePoller` refreshes at different frequencies for `pools / datasets / disks / properties`
- Write operations uniformly call `poller.refresh_once(force_all=True)` upon completion
- `TaskManager` records recent write workflows in memory for operator visibility
- Settings save hot-reloads the runtime instead of requiring manual backend restart
- Auth is lightweight cookie-based login, disabled by default, and can be enabled via the settings page

## Startup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
