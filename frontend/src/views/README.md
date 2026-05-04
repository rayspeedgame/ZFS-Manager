# views

> [中文版本](./README.zh-CN.md)

Route-level page components.

## Files

- `DashboardView.vue`: Overview page
- `DisksView.vue`: Disks and partitions page
- `PoolsView.vue`: Pool page container, responsible for list, drawer, dialog, and topology flows
- `DatasetsView.vue`: Dataset page container, responsible for tree view, drawer, dialog, and create/destroy flows
- `SettingsView.vue`: Backend settings page, responsible for config loading, save, reload, and SSH test

## Notes

- `Dashboard` renders backend summary data
- `Disks` supports partition expansion and pool ownership display
- `Pools` delegates most rendering to `components/pools/`
- `Datasets` delegates most rendering to `components/datasets/`
- `Settings` is responsible for backend connection parameters, polling parameters, and web login settings
