# views

Routed page-level Vue components.

## Files

- `DashboardView.vue`: overview page
- `DisksView.vue`: disks and partitions
- `PoolsView.vue`: pool, topology, and property workflows
- `DatasetsView.vue`: dataset, zvol, and snapshot inventory

## Notes

- `Dashboard` renders backend summary data.
- `Disks` supports partition expansion and pool membership display.
- `Pools` handles property editing, topology mutation, create, destroy, and remove flows.
- `Datasets` handles tree inventory, optional snapshot display, property editing, create, and destroy flows.
