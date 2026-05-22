# Backend

> [中文版本](./README.zh-CN.md)

The backend owns SSH polling, REST write execution, task persistence, schedule execution, and recovery.

## Current Responsibilities

- poll `lsblk`, `blkid`, `zpool`, and `zfs`
- normalize pool, dataset, disk, snapshot, and property state into one shared snapshot
- execute write operations for pools, datasets, and snapshots
- persist tasks and task schedules in SQLite
- recover unfinished tasks after restart
- run recurring `scrub`
- run recurring `snapshot`
- apply schedule-scoped snapshot retention cleanup

## Disk Identity Model

Each disk is normalized into separate display and execution fields:

- `displayName`
  - UI-facing primary name
- `kernelPath`
  - kernel path such as `/dev/sdb`
- `byIdPath`
  - preferred stable alias
- `commandPath`
  - preferred execution path for disks that are not yet part of a pool
- `diskId`
  - stable identifier shown in the UI
- `diskKey`
  - stable local key for saved labels
- `aliases`
  - tolerant lookup aliases used across refreshes

For disks that are already part of a pool:

- `commandPath` is not used
- maintenance commands use the exact member token from `zpool status -L`, exposed as `commandTarget`

## Important Current Modules

- `app/api/`
  - REST API surface
- `app/services/poller.py`
  - state collection, disk identity normalization, plus `scanStatus` / `expandStatus`
- `app/services/task_scheduler.py`
  - recurring workflow scheduler
- `app/services/task_store.py`
  - SQLite-backed persistence
- `app/services/task_recovery.py`
  - startup recovery, reconciliation, and two-phase RAID-Z expansion recovery
- `app/services/snapshot_metadata.py`
  - ZFS user-property definitions for recurring snapshots
- `app/services/snapshot_retention.py`
  - short scheduled snapshot naming and retention execution
- `app/services/pool_replacer.py`
  - replace submission
- `app/services/pool_raidz_expander.py`
  - RAID-Z expansion submission
