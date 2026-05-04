# components/pools

> [中文版本](./README.zh-CN.md)

Pool-specific workflow components.

## Files

- `PoolListPanel.vue`: pool inventory list and entry-point actions
- `PoolDetailDrawer.vue`: readonly facts plus editable pool properties
- `PoolTopologyDrawer.vue`: topology add/remove workflows
- `CreatePoolDrawer.vue`: step-based pool creation UI
- `PoolActionDialogs.vue`: confirmation and result dialogs for pool writes
- `TopologyNode.vue`: recursive topology presentation
- `pool-form-config.js`: pool property fields, topology options, and create-pool config

## Notes

- These components render UI only and emit events upward.
- `PoolsView.vue` owns API calls, live snapshot rebinding, and draft safety.
