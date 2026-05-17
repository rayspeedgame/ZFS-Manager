# Task Recording and Recovery Architecture

> [中文版本](./TaskSystemArchitecture.zh-CN.md)

## Goals

This document defines the task recording, recovery, and presentation architecture for ZFS Manager.

- Unify write operations, long-running tasks, and scheduled jobs under one task system
- Recover task context after backend restarts instead of depending only on in-memory state
- Treat ZFS and system-observable state as the primary source of truth whenever possible
- Leave clean extension points for `scrub`, `replace`, `expansion`, snapshot schedules, replication, and future workflows
- Keep deployment simple for the current single-node project shape

## Core Principles

### 1. Layered Sources of Truth

The task system should not rely on a single truth source.

- `Current ZFS state`
  - Examples: `zpool status`, `zpool list`, `zfs list`, `zfs get`
  - Answers whether the task is still running and what the resource state is now
- `ZFS / system history and events`
  - Examples: `zpool history`, future system log or event integrations
  - Answers what happened and when
- `Application database`
  - Stores task metadata, UI labels, initiators, filters, and aggregated execution logs
  - Must not be treated as the only source of real infrastructure state

### 2. Externalize State, Localize Presentation

Prefer:

- Recovering real task state by re-reading the remote system
- Keeping task cards, timelines, logs, and query indexes in the local database

### 3. Recovery Is Task-Type Specific

Not every task can be recovered the same way. Each task type should declare its own recovery strategy.

Suggested recovery classes:

- `pool_scan_based`
  - Recover from pool scan status such as `zpool status`
  - Examples: `scrub`, `replace/resilver`, some expansion cases
- `state_reconcile_based`
  - Reconcile by checking whether the target state has been reached
  - Examples: snapshot create/delete, property updates
- `scheduler_based`
  - Scheduler state is application-owned, but execution results are reconciled against ZFS state
  - Examples: scheduled snapshot, scheduled scrub
- `app_only`
  - Cannot be reconstructed from ZFS alone and depends on application persistence

## Overall Architecture

Split the task system into five layers:

1. `Task API`
2. `Task Store`
3. `Task Runtime`
4. `Task Recovery Engine`
5. `Task Source Adapters`

## Recommended Storage

### Database Choice

`SQLite` is the recommended first choice:

- No extra service required
- A strong fit for single-node deployment
- More than enough for task history, logs, audit trails, and schedules
- Easy to migrate later to `PostgreSQL` if needed

### Storage Responsibilities

- `SQLite`
  - Task records, task events, execution logs, schedule definitions, recovery markers
- In-memory runtime
  - Active polling subscriptions, hot task indexes, transient recovery state

## Data Model

Use a "main table + events + logs + schedules" shape.

### 1. tasks

Suggested fields:

- `id`
- `kind`
- `category`
- `scope_type`
- `scope_id`
- `scope_name`
- `recovery_mode`
- `status`
- `progress`
- `stage`
- `summary`
- `detail`
- `created_by`
- `source`
- `source_ref`
- `correlation_key`
- `created_at`
- `started_at`
- `finished_at`
- `last_observed_at`
- `last_recovered_at`
- `retry_count`
- `can_cancel`
- `can_retry`
- `metadata_json`

### 2. task_events

Suggested fields:

- `id`
- `task_id`
- `event_type`
- `status_before`
- `status_after`
- `progress`
- `stage`
- `message`
- `payload_json`
- `created_at`

### 3. task_logs

Suggested fields:

- `id`
- `task_id`
- `log_type`
- `command`
- `exit_code`
- `stdout_text`
- `stderr_text`
- `created_at`

### 4. task_schedules

Suggested fields:

- `id`
- `kind`
- `target_scope_type`
- `target_scope_id`
- `enabled`
- `cron_expr`
- `timezone`
- `retention_policy_json`
- `last_run_at`
- `next_run_at`
- `last_task_id`
- `created_at`
- `updated_at`

### 5. task_links

Suggested fields:

- `id`
- `task_id`
- `link_type`
- `linked_scope_type`
- `linked_scope_id`
- `linked_scope_name`

## Task Status Model

Recommended standard states:

- `queued`
- `running`
- `recovering`
- `succeeded`
- `failed`
- `canceled`
- `unknown`
- `needs_attention`

## Recovery Handler Design

Use a registry-based design.

- `TaskRecoveryRegistry`
- `BaseTaskRecoveryHandler`
- `PoolScanRecoveryHandler`
- `SnapshotReconcileRecoveryHandler`
- `ScheduleRecoveryHandler`

Suggested interface:

- `supports(task) -> bool`
- `recover(task, state_snapshot) -> RecoveryResult`
- `reconcile(task, state_snapshot) -> RecoveryResult`

## Startup Recovery Flow

On backend startup:

1. Load all non-terminal tasks
2. Mark them as `recovering`
3. Open SSH and collect a fresh base state snapshot
4. Dispatch each task to its recovery handler
5. Update the main task table and event timeline
6. Mark uncertain tasks as `unknown` or `needs_attention`
7. Re-subscribe still-running tasks to runtime polling

## Periodic Reconciliation

The backend should also periodically reconcile:

- database says running, system says finished
- system shows active scrub or resilver, but no task exists locally

The second case should produce `source=external_detected` tasks.

## Recovery Strategies by Feature

### Scrub

- Recovery mode: `pool_scan_based`
- Primary source: `zpool status`

### Replace / Resilver

- Recovery mode: `pool_scan_based`
- Primary source: `zpool status`

### Single-Disk Expansion

- Prefer `pool_scan_based`
- Fallback to `state_reconcile_based` if continuous progress is not observable

### Snapshot Create / Delete / Rename / Rollback

- Recovery mode: `state_reconcile_based`
- Sources:
  - `zfs list -t snapshot`
  - `zfs get`

### Scheduled Snapshot / Scheduled Scrub

- Recovery mode: `scheduler_based`

## Extensibility Rules

### 1. Use Namespaced Kinds

Recommended format:

- `pool.scrub.start`
- `pool.scrub.stop`
- `pool.replace`
- `pool.expand.single_disk`
- `snapshot.create`
- `snapshot.rollback`
- `schedule.snapshot.run`

### 2. Use JSON Metadata for Feature-Specific Fields

Do not force every task-specific detail into fixed columns.

### 3. Keep an Event Table

Without an event table, history and recovery analysis become fragile.

### 4. Use a Recovery Registry

Each recovery mode or complex task family should own its own handler.

### 5. Allow Externally Detected Tasks

If the system detects an externally started scrub or resilver, it should create an `external_detected` task entry.

## API Recommendations

Suggested additions:

- `GET /api/tasks`
- `GET /api/tasks/{id}`
- `GET /api/tasks/{id}/events`
- `GET /api/tasks/{id}/logs`
- `POST /api/tasks/{id}/retry`
- `POST /api/tasks/{id}/cancel`
- `GET /api/task-schedules`
- `POST /api/task-schedules`
- `PATCH /api/task-schedules/{id}`

## Suggested Implementation Order

### Phase 1

- Introduce `SQLite`
- Add `tasks`, `task_events`, and `task_logs`
- Keep the current in-memory `TaskManager` as the runtime entry point

### Phase 2

- Add `RecoveryRegistry`
- Implement startup recovery
- Start with `scrub` and `replace/resilver`

### Phase 3

- Add `task_schedules`
- Introduce scheduled scrub and scheduled snapshot

### Phase 4

- Support externally detected tasks
- Add timeline UI and richer log inspection
- Add archival, cleanup, and metrics

## Conclusion

The recommended architecture is a combination of durable task persistence, ZFS-backed recovery, and event-oriented extensibility.
