# Task System Architecture

> [中文版本](./TaskSystemArchitecture.zh-CN.md)

## Goals

- Unify write operations, long-running workflows, and scheduled jobs under one task system
- Persist operator-visible history locally
- Recover unfinished work after backend restart
- Prefer ZFS and host state as the truth source for long-running progress
- Leave clean extension points for `scrub`, `replace`, `expansion`, snapshot schedules, and future workflows

## Current Delivered Shape

- Runtime task manager plus SQLite task store
- Startup task reload and active-task reconciliation
- `scrub` recovery based on `zpool status`
- Schedule persistence and background scheduling for weekly `scrub`
- Task records page with pagination and status filtering

## Truth Sources

Use three layers, with clear responsibilities:

1. Current host and ZFS state
   - `zpool status`
   - `zpool list`
   - `zfs list`
   - `zfs get`
2. Event and history sources
   - `zpool history`
   - future host log or event hooks if needed
3. Local application records
   - task rows
   - task logs
   - task schedules
   - operator-facing labels and metadata

The system should not treat local runtime memory as the only truth source.

## Recovery Modes

- `pool_scan_based`
  - Examples: `scrub`, `replace/resilver`, some expansion cases
- `state_reconcile_based`
  - Examples: snapshot create/delete, property updates, create/destroy operations
- `scheduler_based`
  - Examples: scheduled `scrub`, scheduled snapshot
- `app_only`
  - Examples: future UI-only workflows that have no host-visible counterpart

## Storage Model

SQLite remains the current default and recommended first-stage choice because it is:

- simple to deploy
- durable enough for single-node use
- sufficient for task history, schedules, and audit-friendly logs
- easy to migrate later if multi-instance deployment becomes necessary

Recommended shape:

- `tasks`
  - task identity, kind, scope, status, progress, timestamps, metadata
- `task_logs`
  - command and execution output records
- `task_events`
  - later extension for richer timelines
- `task_schedules`
  - recurring workflow definitions

## Current Runtime Flow

### Write-driven tasks

1. REST write endpoint validates payload
2. Task is created and marked running
3. Command executor runs over SSH
4. Backend forces a real-state refresh
5. Task is finalized or updated

### Scheduled tasks

1. Schedule definition is persisted locally
2. Background scheduler checks due rules
3. When due, the scheduler triggers the same underlying workflow
4. Execution still becomes a normal task record

### Startup recovery

1. Load recent persisted tasks
2. Collect a fresh base snapshot
3. Reconcile unfinished tasks against current state
4. Start background polling and scheduling

## Current Frontend Shape

- `TasksView.vue`
  - shows task records and status
  - supports pagination, page-size changes, and status filters
  - keeps filters available even when the current result set is empty
- `SchedulesView.vue`
  - manages scheduled `scrub`
  - reserves a snapshot section for future work
- `PoolDetailDrawer.vue`
  - exposes `scrub` controls and current scan state

## Current API Surface

- `GET /api/tasks`
  - supports `page`, `page_size`, and `status_filter`
- `GET /api/tasks/{task_id}`
- `GET /api/task-schedules`
- `POST /api/task-schedules`
- `PATCH /api/task-schedules/{schedule_id}`
- `DELETE /api/task-schedules/{schedule_id}`
- `POST /api/pools/{pool_name}/scrub/start`
- `POST /api/pools/{pool_name}/scrub/stop`

## Extensibility Guidance

- Keep recovery handlers registry-based
- Keep scheduled workflows routed through the same task system
- Store operator-facing metadata separately from host truth data
- Allow future task-type filters in addition to current status filters
- Preserve room for external task detection, such as a host-side scrub that did not originate from this UI

## Immediate Next Extensions

1. Snapshot scheduling and retention
2. `replace/resilver` recovery handlers
3. More detailed event and log tables
4. Optional background reconciliation that updates active task records even when the task page is not open
