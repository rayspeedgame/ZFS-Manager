# Roadmap

> [中文版本](./Roadmap.zh-CN.md)

## Completed or Active Foundations

- task records and status page
- SQLite-backed task and schedule persistence
- startup recovery and task reconciliation
- manual `scrub`
- recurring `scrub`
- dedicated snapshot page
- snapshot create, delete, rollback, and advanced rollback
- recurring snapshot workflows
- schedule-scoped snapshot retention cleanup
- pool-level `clear`
- device-level `offline / online`
- `replace` plus `resilver` tracking
- RAID-Z `expansion`

## Current Snapshot Direction

- `DatasetsView` still owns quick manual snapshot creation
- `SnapshotsView` is the centralized management surface
- scheduled snapshots use short names such as `scheduled-YYYYMMDD-HHMMSS-random`
- ownership, level, recursion, and retention identity live in ZFS user properties
- cleanup is grouped by schedule identity, so manual snapshots and other schedules stay untouched
- supported schedule levels are:
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## Current Pool-Maintenance Direction

- new-device operations prefer `by-id`
- existing pool-member maintenance must use `commandTarget`
- RAID-Z expansion is exposed at the vdev level, not the leaf-disk level
- RAID-Z expansion recovery now considers:
  - the `expand:` phase
  - the automatic `scrub` phase
  - observed member identity and member-count growth

## Next Priorities

### 1. Snapshot schedule refinement

- edit existing snapshot schedules
- surface strategy ownership and metadata more clearly
- add operator-facing visibility into which snapshots belong to which schedule

### 2. Snapshot retention growth

- `keep latest N` remains the baseline
- add richer tiered retention only when truly needed
- keep the rule that automated cleanup must not affect manual snapshots

### 3. Pool maintenance growth

- clearer candidate-disk eligibility for `replace`
- clearer candidate-disk eligibility for RAID-Z `expansion`
- richer maintenance summary and audit context

### 4. Documentation and audit depth

- keep schedule, retention, task recovery, and pool-maintenance docs aligned
- continue improving operator-visible task logs and audit details
