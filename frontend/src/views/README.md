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
- disk table includes an inline SMART health column (PASS/FAIL badge + temperature) sourced from `smart_overview` in the WebSocket snapshot
- full SMART details open in a `ConfirmDialog` (result mode) with temperature, power-on hours, protocol, serial, firmware, and scrollable attribute table with status badges
- manual refresh in the detail view currently asks the backend for a complete state refresh rather than polling only the selected disk

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
- existing-pool topology updates accept auxiliary vdevs only; adding a new data vdev is not supported

### `SnapshotsView`

- supports search, pool/dataset/type filters, pagination, and sorting
- supports detail, creation, deletion, and safe/forced rollback, with action availability supplied by backend capability flags

### `SchedulesView`

- supports recurring snapshot levels from minutely through monthly
- supports recurring `scrub`
- scrub currently supports weekly frequency only; schedules can be created, enabled/disabled, and deleted, while a complete edit form remains unimplemented

### `TasksView`

- supports pagination, status filtering, and auto refresh
- long-running task details show command logs
- RAID-Z expansion tasks move through:
  - the `expand` phase
  - the automatic `scrub` phase

### `SettingsView`

- reads and saves SSH, polling, login, and disk-label configuration
- provides SSH connection testing and separate active/idle SMART polling intervals
