# Roadmap

> [中文版本](./Roadmap.zh-CN.md)

This document tracks the ZFS Manager feature roadmap, delivered milestones, and the recommended next implementation order.

## Current Progress

The following stages are already delivered or have a usable foundation:

- Task system baseline
  - Existing write operations already create task records
  - Task list and task detail APIs are available
  - The frontend has a dedicated task records page
- Task persistence and recovery
  - SQLite persistence is connected
  - Recent task history reloads after backend restart
  - Startup reconciliation exists for unfinished tasks
- `scrub` baseline support
  - Manual `scrub` start is available
  - Manual `scrub` stop is available
  - Pool details show `scrub` state, progress, ETA, and related messaging
  - `scrub` progress can be recovered from `zpool status`
- Scheduled workflow baseline
  - A dedicated schedules page exists
  - Weekly scheduled `scrub` definitions can be created, enabled, disabled, and deleted
  - Snapshot scheduling has a reserved placeholder area
- Task records page usability improvements
  - The page is now named "Task Records & Status"
  - Records are paged instead of fully loaded
  - Status filtering is supported
  - Empty-filter results no longer break the page shell

## Planning Principles

- Continue using the current `state collection + REST writes + forced refresh` model instead of introducing a parallel local state system
- Route long-running workflows through the task system instead of having each feature maintain isolated progress state
- Let the backend emit explicit capability fields; keep the frontend focused on consuming them rather than inferring operational risk
- Prefer ZFS and host-readable truth sources first, and local task records second
- Keep the record and recovery system extensible so it can absorb `scrub`, `replace`, `expansion`, snapshot scheduling, and audit workflows cleanly

## Landed Work

### 1. Task system

Delivered:

- Unified task data model
- Task list and detail endpoints
- Dedicated task records page
- SQLite persistence
- Startup recovery framework
- Task reconciliation
- Pagination and status filtering for task records

Current status set:

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`
- `recovering`
- `unknown`
- `needs_attention`

### 2. Pool scrub

Delivered:

- Manual `scrub` start
- Manual `scrub` stop
- Pool detail `scrub` status presentation
- Progress and ETA parsing from `zpool status`
- Recovery of active `scrub` state after backend restart

### 3. Scheduled scrub

Delivered:

- Dedicated schedules page
- Weekly per-pool `scrub` schedule creation
- Enable, disable, and delete actions
- Schedule persistence in the local task database
- Schedule execution through the shared task system

## Next Focus Areas

### 1. Snapshot management

Goals:

- Snapshot list view
- Manual snapshot creation
- Snapshot deletion
- Snapshot rollback or restore
- Scheduled snapshots
- Retention and automatic cleanup

Current recommendation:

- Keep the first stage inside `DatasetsView`
- Re-evaluate a dedicated snapshot page once scheduling, retention, and batch operations become prominent

### 2. Pool device replace

Goals:

- Replacement candidate discovery
- Preflight validation
- Trigger `replace`
- Track `resilver` progress through the task system

Implementation requirements:

- Backend should expose explicit fields such as `canReplace`, `replaceCandidates`, and denial reasons
- Recovery should prefer `zpool status`

### 3. Single-disk expansion

Goals:

- Eligibility detection
- Trigger expansion
- Track long-running progress through the task system

Implementation requirements:

- Start with read-only eligibility checks before exposing execution entry points
- Reuse parts of the `replace/resilver` recovery infrastructure

### 4. Snapshot scheduling and retention

Goals:

- Fill in the snapshot section on the schedules page
- Persist snapshot schedule definitions
- Add retention rules and cleanup execution
- Register schedule runs as normal task records

### 5. Operations hardening

Suggested additions:

- Snapshot retention and cleanup reporting
- `offline/online` device operations
- Operator-visible audit history
- Pool or disk alerts
- More granular permissions
- Better failure summaries and operator guidance

## Recommended Implementation Order

1. Baseline snapshot management
2. Scheduled snapshots and retention
3. `replace`
4. `single-disk expansion`
5. `offline/online`, audit, alerting, and other hardening steps

## Task System Evolution

To preserve extensibility, the task system should continue moving in these directions:

- Add task schedule, task event, and task log tables
- Keep recovery handlers registry-based instead of collecting all logic in one file
- Distinguish recovery modes:
  - `pool_scan_based`
  - `state_reconcile_based`
  - `scheduler_based`
  - `app_only`
- Support detection of externally started workflows that were not launched from this UI

## Snapshot UI Direction

For the question of whether snapshots should have a dedicated page, the current recommendation remains staged.

### Option A: Keep snapshots in `DatasetsView` first

Advantages:

- Natural fit with dataset and zvol context
- Reuses the existing tree selection model
- Lower first-version implementation cost

Limits:

- Large snapshot inventories can make the dataset page noisy
- Scheduling, retention, and batch operations become harder to present cleanly

### Option B: Split into a dedicated snapshot page later

Recommended when:

- Snapshot inventories grow significantly
- Scheduled snapshots and retention become core workflows
- Cross-dataset filtering, bulk operations, or fuller history views become important

### Current conclusion

1. Deliver baseline snapshot management inside `DatasetsView`
2. Introduce a dedicated snapshot page later if scheduling, retention, and bulk management become substantial
