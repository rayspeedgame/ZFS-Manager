# Backend

> [中文版](./README.zh-CN.md)

The backend owns SSH polling, REST write execution, task persistence, schedule execution, and recovery.

## Current Responsibilities

- Poll host state from `lsblk`, `blkid`, `zpool`, and `zfs`
- Normalize pool, dataset, disk, and property state into one application snapshot
- Execute write operations for pools, datasets, and snapshots
- Persist tasks and task schedules in SQLite
- Recover unfinished tasks after restart
- Run scheduled `scrub`
- Run scheduled `snapshot`
- Apply schedule-scoped snapshot retention cleanup

## Important Current Modules

- `app/api/`: REST API surface
- `app/services/poller.py`: state collection and snapshot assembly
- `app/services/task_scheduler.py`: recurring workflow scheduler
- `app/services/snapshot_metadata.py`: ZFS user-property definitions for scheduled snapshots
- `app/services/snapshot_retention.py`: short scheduled snapshot naming and retention planning
- `app/services/task_store.py`: SQLite-backed persistence
- `app/services/task_recovery.py`: startup recovery and reconciliation

## Current Snapshot Scheduling Rule

- Scheduled snapshot names stay short
- Schedule identity is written into ZFS user properties
- Cleanup matches snapshots by stored schedule ownership instead of parsing long names
