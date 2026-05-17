# Backend

> [中文版本](./README.zh-CN.md)

The backend currently handles five things: collecting remote host state, normalizing raw output into unified snapshots, executing ZFS/ZPool write operations, persisting operator-visible tasks, and recovering unfinished workflows after restart.

## Main Responsibilities

- Execute read-only commands via SSH to collect:
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status/list/get`
  - `zfs list/get`
- Parse raw output into unified `meta + data` snapshots
- Expose REST endpoints for:
  - state read and forced refresh
  - settings read, save, and SSH test
  - login status, login, and logout
  - pool and dataset write operations
  - `scrub` start and stop
  - task list, task detail, and task schedules
- Push latest snapshots via WebSocket
- Persist tasks and schedules in SQLite, then reconcile unfinished workflows at startup

## Directory Structure

- `app/api/`: REST and WebSocket entry points
- `app/core/`: Configuration, auth, shared state, and runtime infrastructure
- `app/schemas/`: Pydantic request, response, snapshot, task, and schedule models
- `app/services/`: Polling, state aggregation, writes, tasks, schedules, and recovery
- `app/ssh/`: SSH client, command definitions, and parsers
- `config/`: Active configuration directory and `tasks.sqlite3`
- `tests/fixtures/`: Fixture-mode input samples

## Current Implementation Focus

- `StatePoller` refreshes at different frequencies for `pools / datasets / disks / properties`
- Write operations still call `poller.refresh_once(force_all=True)` after completion
- `TaskManager + SQLiteTaskStore` provide a combined in-memory runtime and SQLite persistence model
- `TaskRecoveryService` reconciles unfinished tasks at startup and during task reads
- `TaskScheduler` persists and runs recurring `scrub` schedules
- `poller.py` generates structured `scanStatus` for each pool
- Auth remains a lightweight cookie-based login, disabled by default and configurable from settings

## Startup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
