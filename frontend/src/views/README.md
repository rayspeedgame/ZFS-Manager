# views

> [中文版本](./README.zh-CN.md)

Route-level page components.

## Files

- `DashboardView.vue`: Overview page
- `DisksView.vue`: Disks and partitions page
- `PoolsView.vue`: Pool page container for list, drawer, dialog, topology, and scrub flows
- `DatasetsView.vue`: Dataset page container for tree, drawer, dialog, and create/destroy flows
- `SchedulesView.vue`: Scheduled workflow page for weekly scrub rules and future snapshot scheduling
- `TasksView.vue`: Task records and status page with pagination, filters, and detail pane
- `SettingsView.vue`: Backend settings page for config loading, save, reload, and SSH test

## Notes

- `Dashboard` renders backend summary data
- `Disks` supports partition expansion and pool ownership display
- `Pools` delegates most rendering to `components/pools/`
- `Datasets` delegates most rendering to `components/datasets/`
- `Schedules` is the first dedicated page for recurring workflows
- `Tasks` keeps task filters visible even when the current filter produces zero records
- `Settings` handles backend connection, polling, and web-login settings
