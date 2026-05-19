# Target

> [中文版](./target.zh-CN.md)

## Current Product Goal

Build ZFS Manager into a practical ZFS web interface for single-node or small lab environments, so operators can complete common pool, dataset, snapshot, task, and scheduling workflows without constantly dropping to the CLI.

## Delivered Capabilities

### Pool workflows

- Pool health, capacity, and status overview
- Topology visualization
- Editable pool properties
- Add `log`, `cache`, `special`, `dedup`, and `spare` devices
- Create and destroy pools
- Remove supported topology targets
- Start and stop `scrub`
- Show `scrub` state, progress, and ETA in pool details

### Dataset and snapshot workflows

- Dataset and zvol inventory
- Expandable dataset tree
- Create and destroy dataset or zvol children
- Edit dataset properties
- Quick snapshot creation from `DatasetsView`
- Dedicated `SnapshotsView`
- Snapshot list pagination, filtering, detail view, delete, and rollback
- Advanced rollback modes for safe, `-r`, and `-R` rollback

### Task and schedule workflows

- Dedicated task records and status page
- Unified task model for pool, dataset, and snapshot writes
- SQLite-backed task persistence
- Startup recovery and reconciliation for unfinished tasks
- Scheduled `scrub`
- Scheduled `snapshot`
- Snapshot schedule retention cleanup with per-schedule ownership
- Snapshot schedule levels:
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## Current Architecture Direction

- `SnapshotsView` is the centralized snapshot management surface
- `DatasetsView` remains the lightweight initiation surface for snapshot creation
- Scheduled snapshots now use short snapshot names and store strategy ownership in ZFS user properties
- Retention is matched by schedule identity, so scheduled cleanup does not affect manual snapshots or snapshots created by other schedules
- The schedules page now hosts both recurring `scrub` and recurring `snapshot` definitions

## Next Steps

- Sync current scheduled snapshot and retention behavior into operator documentation
- Add richer scheduled snapshot editing and policy inspection
- Extend retention beyond keep-latest into tiered daily/weekly/monthly retention when needed
- Continue expanding pool maintenance workflows such as replace, resilver tracking, and expansion
