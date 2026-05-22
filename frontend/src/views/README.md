# views

> [中文版本](./README.zh-CN.md)

This directory holds route-level page components.

## Main Pages

- `DashboardView.vue`
  - overview page
- `DisksView.vue`
  - disks and partitions page
- `PoolsView.vue`
  - pool page container
- `DatasetsView.vue`
  - dataset page container with quick manual snapshot creation
- `SnapshotsView.vue`
  - dedicated snapshot management page
- `SchedulesView.vue`
  - recurring `scrub` and recurring `snapshot`
- `TasksView.vue`
  - task records and status page
- `SettingsView.vue`
  - backend settings page

## Current Notes

### `DisksView`

- uses the normalized disk identity model
- main title comes from `displayName`
- secondary lines show `kernelPath` and `byIdPath`
- custom labels persist through `diskKey`

### `PoolsView`

- new-device operations prefer `commandPath`
- existing pool-member maintenance uses `commandTarget`
- topology displays prefer aliases instead of raw execution tokens
- now owns:
  - `scrub`
  - `clear`
  - `offline / online`
  - `replace`
  - RAID-Z `expansion`

### `SchedulesView`

- supports recurring snapshot levels from minutely through monthly
- supports recurring `scrub`

### `TasksView`

- supports pagination, status filtering, and auto refresh
- long-running task details show command logs
- RAID-Z expansion tasks move through:
  - the `expand` phase
  - the automatic `scrub` phase
