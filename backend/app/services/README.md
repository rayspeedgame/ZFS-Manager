# services

> [中文版本](./README.zh-CN.md)

This directory holds backend services for polling, task orchestration, scheduling, snapshot policy, and pool-maintenance execution.

## Main Files

- `poller.py`
  - collects SSH state, normalizes disk identity, and builds the shared snapshot
- `task_manager.py`
  - task registration, updates, and query helpers
- `task_store.py`
  - SQLite-backed persistence
- `task_recovery.py`
  - startup recovery and reconciliation
- `task_scheduler.py`
  - recurring `scrub` and recurring `snapshot`
- `snapshot_metadata.py`
  - ZFS user-property definitions
- `snapshot_retention.py`
  - short recurring snapshot naming and retention cleanup
- `pool_scrubber.py`
  - `scrub` submission
- `pool_maintainer.py`
  - `clear`, `offline`, and `online`
- `pool_replacer.py`
  - `replace`
- `pool_raidz_expander.py`
  - RAID-Z `expansion`

## Current Conventions

### Disk and member identity

`poller.py` builds both disk-level and pool-member-level identity:

- disk rows expose `displayName`, `kernelPath`, `byIdPath`, `commandPath`, `diskId`, `diskKey`, and `aliases`
- pool leaf members expose `displayLabel`, `kernelPath`, `byIdPath`, `commandTarget`, `rawCommandTarget`, and `aliases`

Partition-backed members also inherit the parent disk’s whole-disk `by-id` aliases so recovery code can still match the same physical disk when one side uses the whole-disk path and the other side uses a `-part1` path.

### Pool maintenance commands

- new-device operations prefer `commandPath`
- existing pool-member maintenance must use `commandTarget`

### RAID-Z expansion recovery

`task_recovery.py` now observes all of the following before closing the task:

- the `expand:` section
- the automatic `scrub` section
- the new member appearing in the target vdev
- the member count increasing
