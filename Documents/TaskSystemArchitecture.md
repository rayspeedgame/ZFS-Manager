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
   - `zpool history`
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
  - in-app delete confirmations
- `SnapshotsView.vue`
  - centralized snapshot management and rollback

## Immediate Next Extensions

1. Editing existing snapshot schedules
2. Richer retention reporting
3. `replace/resilver` recovery handlers
4. Background reconciliation updates even when the task page is closed
