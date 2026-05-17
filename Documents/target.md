# Target

> [中文版本](./target.zh-CN.md)

## Current Product Goal

Build ZFS Manager into a practical ZFS web interface for single-node or small lab environments, so operators can complete common pool, dataset, task, and scheduling workflows without constantly dropping to the CLI.

## Delivered Capabilities

### Pool workflows

- Pool health, capacity, and status overview
- Topology visualization
- Editable pool properties
- Add `log`, `cache`, `special`, `dedup`, and `spare` devices
- Create new pools with:
  - pool properties
  - root dataset properties
  - step-based data-vdev and auxiliary-vdev planning
- Destroy pools
- Remove supported topology targets
- Start and stop `scrub`
- Show current pool `scan` / `scrub` status, progress, and ETA inside pool details

### Dataset workflows

- Dataset and zvol inventory
- Expandable dataset tree
- Optional snapshot visibility
- Create dataset and zvol children
- Edit dataset properties
- Destroy dataset and zvol entries

### Task and schedule workflows

- Dedicated task records page for recent write operations and long-running workflows
- Unified task model for pool and dataset writes
- Task detail view with status, progress, stage, timestamps, and command logs
- SQLite-backed task persistence
- Startup recovery for recent unfinished tasks
- `scrub` progress recovery based on `zpool status`
- Dedicated schedules page for recurring tasks
- Weekly scheduled `scrub` definitions with enable, disable, and delete actions
- Placeholder panel reserved for future scheduled snapshot workflows
- Paged task records with page-size controls and status filtering

### UI capabilities

- English and Chinese language switching
- Initial locale detection from browser language
- Local persistence of user language preference
- Translated navigation, dashboard, pools, datasets, schedules, task records, settings, and dialog copy

## Frontend Direction

- `PoolsView` and `DatasetsView` remain page containers
- `TasksView` is the shared visibility layer for task records, long-running workflows, and command logs
- `SchedulesView` owns recurring workflow definitions such as scheduled `scrub`
- Pool details in `PoolsView` now carry the `scrub` controls and live status summary
- Shared property editors, dialogs, command-result views, and utility panels remain in `frontend/src/components/common/`
- User-visible text should continue to flow through i18n keys

## Backend Direction

- Write operations continue to register operator-visible tasks uniformly
- The task system currently uses an in-memory runtime plus SQLite persistence model
- Startup order is:
  1. load persisted task history
  2. refresh remote state
  3. reconcile unfinished tasks
  4. start background polling and scheduling
- `scrub` is the first fully connected long-running workflow that participates in recovery
- Scheduled workflows now go through the same task infrastructure instead of bypassing it
- Future `replace`, `resilver`, `expansion`, and snapshot schedules should reuse the same recovery model

## Next Steps

- Move active-task reconciliation further into background polling, not only task reads
- Add more pool-level long-running recoverers, starting with `replace/resilver`
- Fill in snapshot scheduling and retention logic on top of the schedules page
- Continue expanding task events, logs, and operator-facing audit context
- Keep extending i18n and state hints for newly added workflows
