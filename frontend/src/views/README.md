# views

> [中文版](./README.zh-CN.md)

Route-level page components.

## Files

- `DashboardView.vue`: overview page
- `DisksView.vue`: disks and partitions page
- `PoolsView.vue`: pool page container
- `DatasetsView.vue`: dataset page container with quick manual snapshot creation
- `SnapshotsView.vue`: dedicated snapshot management page
- `SchedulesView.vue`: recurring `scrub` and recurring `snapshot` page
- `TasksView.vue`: task records and status page
- `SettingsView.vue`: backend settings page

## Notes

- `SchedulesView` now supports minutely through monthly snapshot schedules
- Schedule deletion uses the same in-app confirmation dialog pattern as other destructive flows
- `SnapshotsView` remains the centralized snapshot management surface
