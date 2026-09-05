# Task System Architecture

> [中文版](./TaskSystemArchitecture.zh-CN.md)

## Goals

- Unify writes, long-running workflows, and scheduled jobs under one task system
- Persist operator-visible history locally
- Recover unfinished work after backend restart
- Prefer ZFS and host state as the truth source for long-running progress
- Keep clean extension points for `scrub`, snapshot schedules, retention, `replace`, and future workflows

## Current Delivered Shape

- Runtime task manager plus SQLite task store
- Startup task reload and active-task reconciliation
- `scrub` recovery based on `zpool status`
- `replace/resilver` recovery based on `zpool status` and normalized topology
- RAID-Z expansion recovery using `expand:`, automatic `scrub`, and vdev member changes
- Schedule persistence and background scheduling
- Scheduled `scrub`
- Scheduled `snapshot`
- Schedule-scoped snapshot retention cleanup
- Task records page with pagination and status filtering

## Truth Sources

Use three layers with clear boundaries:

1. Host and ZFS state
   - `zpool status`
   - `zpool list`
   - `zfs list`
   - `zfs get`
2. Event and history sources
   - `zpool history` (planned supporting evidence; not currently integrated)
   - future host log or event hooks
3. Local application records
   - task rows
   - task schedules
   - task logs
   - operator-facing metadata

## Current Snapshot Scheduling Rule

- Scheduled snapshots use short names
- Ownership and retention identity are written into ZFS user properties
- Cleanup matches snapshots by stored schedule identity
- Recursive schedules still retain snapshots per dataset rather than one global count

## Current Frontend Shape

- `TasksView.vue`
  - paged task records and status filters
- `SchedulesView.vue`
  - recurring `scrub`
  - recurring `snapshot`
  - schedule creation, enable/disable, and deletion
  - in-app delete confirmations
- `SnapshotsView.vue`
  - centralized snapshot management and rollback

## Current Reconciliation Triggers

- after the backend starts and produces its first state refresh
- after relevant pool-maintenance actions or a scheduled scrub force a state refresh
- when task list or task detail APIs are requested

As a result, `scrub`, `resilver`, and RAID-Z expansion reconcile against current state at those points. A reconciliation loop that runs independently of request traffic is not implemented yet.

## Immediate Next Extensions

1. A complete edit-existing-schedule UI (the UI currently supports enable/disable and delete; backend PATCH already supports title, pattern, and metadata)
2. Richer retention reporting
3. Background reconciliation updates even when the task page is closed
4. Stronger history and audit evidence for short writes whose result cannot be safely inferred from current state
