# Roadmap

> [中文版本](./Roadmap.zh-CN.md)

This document tracks the ZFS Manager product roadmap, the work already completed, and the recommended order for upcoming development.

## Current Progress

The following layers are already complete or usable today:

- Task system foundation
  - Shared task model, task list/detail APIs, and a frontend task page
  - Existing write operations already create task records
- Task system persistence and recovery
  - `SQLite` persistence is in place
  - Recent task history is reloaded on backend startup
  - A startup reconciliation framework exists for unfinished tasks
- `scrub` baseline support
  - Manual `scrub` start is available
  - Manual `scrub` stop is available
  - Pool details show `scrub` state, progress, ETA, and related messaging
  - `scrub` progress can be recovered from `zpool status`

## Planning Principles

- Continue building on the existing `state polling + REST writes + forced refresh` architecture instead of introducing a parallel state model.
- Route long-running operations through the shared task system instead of letting each workflow invent its own progress handling.
- Keep capability and safety checks authoritative in the backend so the frontend consumes explicit results.
- Prefer ZFS or system-readable truth sources over backend-only runtime memory.
- Keep the record and recovery system extensible so it can absorb `scrub`, `replace`, `expansion`, snapshot scheduling, and audit workflows cleanly.

## What Is Already Delivered

### 1. Task System

Completed:

- Shared task data model
- Task list and task detail APIs
- Task page and baseline status presentation
- `SQLite` persistence
- Startup recovery framework
- Active task reconciliation

Core task states currently supported:

- `queued`
- `running`
- `succeeded`
- `failed`
- `canceled`
- `recovering`
- `unknown`

### 2. Pool Scrub

Completed:

- Manual `scrub` start
- Manual `scrub` stop
- Current scan state in pool details
- Progress, ETA, and completion parsing from `zpool status`
- Task recovery for `scrub` after backend restart

## Next Major Work

### 1. Scheduled Scrub

Goals:

- Configure scheduled `scrub` per pool
- Show next run, last run, and recent results
- Route triggered executions through the task system

Suggested approach:

- Add a scheduler data model and scheduler service
- Persist schedules locally in the database
- Continue using the task system for each actual execution record

### 2. Snapshot Management

Goals:

- Snapshot listing
- Manual snapshot creation
- Snapshot deletion
- Snapshot rollback or restore
- Scheduled snapshots
- Retention policies and automatic cleanup

Current recommendation:

- Keep the first implementation inside `DatasetsView`
- Re-evaluate a dedicated snapshot page once scheduling, retention, and batch operations become prominent

### 3. Pool Device Replace

Goals:

- Replace candidate discovery
- Pre-flight eligibility checks
- `replace` initiation
- `resilver` tracking through the task system

Implementation requirements:

- The backend should expose explicit capability fields such as `canReplace`, `replaceCandidates`, and failure reasons
- Recovery should primarily rely on `zpool status`

### 4. Single-Disk Expansion

Goals:

- Eligibility checks for single-disk expansion
- Expansion trigger
- Long-running progress tracking through the task system

Implementation requirements:

- Read-only qualification checks should come first
- Reuse part of the same progress and recovery infrastructure as `replace/resilver`

### 5. Supporting Operations

Recommended additions:

- Snapshot retention and automatic cleanup
- `offline/online` device actions
- Operation audit history
- Pool or disk alerts
- Finer-grained permission handling
- Clearer failure summaries and operator guidance

## Recommended Delivery Order

1. Scheduled `scrub`
2. Baseline snapshot management
3. Scheduled snapshots and retention
4. `replace`
5. `single-disk expansion`
6. `offline/online`, audit, alerts, and related follow-on operations

## Task System Evolution

To keep the design extensible, the task system should continue evolving in these directions:

- Add task schedule, task event, and task log tables
- Use registrable recovery handlers instead of putting every recovery rule into one file
- Distinguish recovery strategies such as:
  - `pool_scan_based`
  - `state_reconcile_based`
  - `scheduler_based`
  - `app_only`
- Detect and surface external tasks that were not launched from this frontend but are observable in the system

## Snapshot UI Direction

For the question of whether snapshots should have a dedicated page, the current recommendation remains staged.

### Option A: Keep snapshots in `DatasetsView` first

Pros:

- Naturally aligned with dataset and zvol context
- Reuses the current tree selection workflow
- Lower implementation cost for the first release

Limitations:

- Large snapshot inventories can make the dataset page noisy
- Scheduling, retention, and batch workflows become harder to present cleanly

### Option B: Split into a dedicated snapshot page later

Best fit when:

- Snapshot volume becomes large
- Scheduled snapshots and retention become core workflows
- Cross-dataset filtering, batch actions, or richer history views become important

### Current Conclusion

Use a staged approach:

1. Deliver baseline snapshot management inside `DatasetsView`
2. Introduce a dedicated snapshot page later if scheduling, retention, and bulk management become substantial
