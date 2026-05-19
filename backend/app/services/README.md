# services

> [中文版](./README.zh-CN.md)

This layer owns backend runtime behavior, especially polling, write execution, task persistence, recurring scheduling, and recovery.

## Important Files

- `poller.py`: collects SSH state and assembles the shared app snapshot
- `task_manager.py`: runtime task lifecycle management
- `task_store.py`: SQLite-backed task and schedule persistence
- `task_recovery.py`: startup recovery and reconciliation
- `task_scheduler.py`: recurring workflow scheduler for `scrub` and `snapshot`
- `snapshot_metadata.py`: ZFS user-property keys for scheduled snapshots
- `snapshot_retention.py`: scheduled snapshot naming and keep-latest retention planning
- `snapshot_query.py`: reads snapshot ownership fields back from properties

## Current Design Notes

- Scheduled snapshots now rely on ZFS user properties for ownership and retention identity
- Retention cleanup is schedule-scoped and dataset-aware
- Write endpoints always refresh live state instead of mutating frontend assumptions directly
