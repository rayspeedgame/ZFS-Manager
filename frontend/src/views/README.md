# views

Routed page-level Vue components.

## Files

- `DashboardView.vue`: overview page
- `DisksView.vue`: disks and partitions
- `PoolsView.vue`: page container for pool list, drawers, dialogs, and topology workflows
- `DatasetsView.vue`: page container for dataset tree, drawers, dialogs, and create/destroy workflows

## Notes

- `Dashboard` renders backend summary data.
- `Disks` supports partition expansion and pool membership display.
- `Pools` now delegates most rendering to `components/pools/` and keeps page-level draft state plus API calls in the view.
- `Datasets` now delegates most rendering to `components/datasets/` and keeps page-level draft state plus API calls in the view.
