# services

> [中文版本](./README.zh-CN.md)

This layer owns the backend runtime behavior, especially polling, caching, write execution, task persistence, scheduling, and recovery.

## File Descriptions

- `poller.py`: Schedules SSH refresh tasks, maintains snapshot cache, and generates `summary / disks / pools / datasets`
- `pool_creator.py`: Generates and executes atomic `zpool create`
- `property_updater.py`: Executes `zpool set`
- `topology_updater.py`: Executes `zpool add`
- `pool_destroyer.py`: Executes `zpool destroy`
- `pool_remover.py`: Executes `zpool remove`
- `pool_scrubber.py`: Executes `zpool scrub` and `zpool scrub -s`
- `dataset_creator.py`: Executes `zfs create`
- `dataset_property_updater.py`: Executes `zfs set`
- `dataset_destroyer.py`: Executes `zfs destroy`
- `task_manager.py`: Runtime task lifecycle management
- `task_store.py`: SQLite-backed task and schedule persistence
- `task_recovery.py`: Recovery registry and reconciliation service
- `task_scheduler.py`: Recurring workflow scheduler

## Current Design

- `StatePoller` refreshes `pools / datasets / disks / properties` at different frequencies
- Write endpoints do not directly mutate snapshots; they re-collect real host state
- Dataset hierarchy, parent-child relationships, and display order are normalized by the backend before reaching the frontend
- Task execution and task presentation are separate concerns:
  - executors run commands
  - task services persist and reconcile operator-visible records
- Scheduled `scrub` runs through the same task system as manual operations
