# components/pools

> [中文版本](./README.zh-CN.md)

Pool-specific workflow components.

## Files

- `PoolListPanel.vue`: Pool inventory list and entry-point actions
- `PoolDetailDrawer.vue`: Pool facts, editable properties, and scrub status/actions
- `PoolTopologyDrawer.vue`: Topology add/remove workflows
- `CreatePoolDrawer.vue`: Step-based pool creation UI
- `PoolActionDialogs.vue`: Confirmation and result dialogs for pool writes
- `TopologyNode.vue`: Recursive topology presentation
- `pool-form-config.js`: Pool property fields, topology options, and create-pool config

## Notes

- These components render UI and emit events upward
- `PoolDetailDrawer.vue` now includes a dedicated scrub section with:
  - status summary
  - progress and ETA
  - start and stop controls
- `PoolsView.vue` still owns API calls, live snapshot rebinding, and draft safety
