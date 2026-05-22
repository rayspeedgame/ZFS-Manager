# Target

> [中文版本](./target.zh-CN.md)

## Current Product Goal

Build ZFS Manager into a practical ZFS web interface for single-node or small lab environments so operators can complete common pool, dataset, snapshot, task, and schedule workflows without constantly dropping to the CLI.

## Delivered Capabilities

### Pool workflows

- pool health, capacity, and state overview
- topology visualization
- editable pool properties
- add `log`, `cache`, `special`, `dedup`, and `spare` devices
- create and destroy pools
- remove supported topology targets
- start and stop `scrub`
- show `scrub` state, progress, and ETA in pool details
- pool-level `clear`
- device-level `offline / online`
- device-level `replace`
- `resilver` tracking and recovery
- RAID-Z `expansion`

### Dataset and snapshot workflows

- dataset and zvol inventory
- expandable dataset tree
- create and destroy dataset or zvol children
- edit dataset properties
- quick snapshot creation from `DatasetsView`
- dedicated `SnapshotsView`
- snapshot list pagination, filtering, detail view, delete, and rollback
- advanced rollback modes for safe, `-r`, and `-R` rollback

### Task and schedule workflows

- dedicated task records and status page
- unified task model for pool, dataset, and snapshot writes
- SQLite-backed task persistence
- startup recovery and reconciliation for unfinished tasks
- recurring `scrub`
- recurring `snapshot`
- schedule-scoped snapshot retention cleanup
- snapshot schedule levels:
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## Current Architecture Direction

- `SnapshotsView` is the centralized snapshot management surface
- `DatasetsView` remains the lightweight entry point for manual snapshot creation
- scheduled snapshots use short names and store ownership in ZFS user properties
- retention is matched by schedule identity, so cleanup does not affect manual snapshots or snapshots from other schedules
- `SchedulesView` hosts both recurring `scrub` and recurring `snapshot`
- pool maintenance now separates display identity from execution identity so path churn does not break commands

## Next Steps

- keep improving recurring snapshot editing and schedule visibility
- extend retention into richer tiered rules only when needed
- continue improving `replace` and RAID-Z `expansion` candidate explanations and audit detail
