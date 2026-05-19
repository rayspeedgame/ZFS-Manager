# Roadmap

> [中文版](./Roadmap.zh-CN.md)

## Completed or Active Foundations

- Unified task records and status page
- SQLite-backed task and schedule persistence
- Startup recovery and task reconciliation
- Manual `scrub` with progress display and recovery
- Scheduled `scrub`
- Dedicated snapshot page
- Snapshot create, delete, rollback, and advanced rollback modes
- Scheduled snapshot workflows
- Snapshot retention cleanup based on schedule-scoped ownership

## Current Snapshot Direction

The current snapshot direction is now stable enough to treat as the baseline:

- Manual snapshots can still be created directly from `DatasetsView`
- Centralized snapshot management lives in `SnapshotsView`
- Scheduled snapshots use short names such as `scheduled-YYYYMMDD-HHMMSS-random`
- Strategy ownership, level, recursion, and retention identity are stored in ZFS user properties
- Retention cleanup matches snapshots by schedule identity, not by long names
- Supported schedule levels now include:
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## Next Development Priorities

### 1. Snapshot schedule refinement

- Edit existing snapshot schedules
- Surface strategy metadata more clearly in the UI
- Add operator-facing visibility into which snapshots belong to which schedule

### 2. Snapshot retention growth

- Keep-latest is the current baseline
- Add richer tiered retention only when needed
- Preserve the rule that scheduled cleanup must not affect manual snapshots

### 3. Pool maintenance growth

- Device replace
- Resilver progress and recovery
- Single-disk expansion
- Additional pool maintenance actions such as offline and online

### 4. Documentation and audit depth

- Keep schedule, retention, and task behavior aligned across docs
- Expand task logs and operator-visible audit context

## Design Rules To Keep

- Prefer ZFS and host state as the source of truth for long-running workflows
- Keep snapshot names short and low-risk
- Store scheduled snapshot ownership and cleanup identity in ZFS user properties
- Keep scheduled cleanup isolated to the schedule that created the snapshots
