# components/pools

> [中文版本](./README.zh-CN.md)

This directory holds pool-specific workflow components.

## Main Files

- `PoolListPanel.vue`
  - pool inventory list and entry-point actions
- `PoolDetailDrawer.vue`
  - pool details, properties, `scrub`, and `clear`
- `PoolTopologyDrawer.vue`
  - topology edits, device maintenance, replace, and RAID-Z expansion
- `CreatePoolDrawer.vue`
  - step-based pool creation UI
- `PoolActionDialogs.vue`
  - shared confirmation and result dialogs for pool writes
- `TopologyNode.vue`
  - recursive topology presentation
- `pool-form-config.js`
  - pool property fields, topology options, and create-pool config

## Current Conventions

- these components mainly render UI and emit events upward
- `PoolDetailDrawer.vue` owns pool-level maintenance summary
- `PoolTopologyDrawer.vue` owns device-level and vdev-level maintenance entry points

### Topology identity fields

Topology components now use three kinds of fields together:

- display fields
  - `displayLabel`
- helper identity fields
  - `kernelPath`
  - `byIdPath`
  - `aliases`
- execution field
  - `commandTarget`

### Delivered maintenance actions

- `offline / online`
- `replace`
- RAID-Z `expansion`

The RAID-Z expansion button lives on the vdev item, not on an individual leaf disk.
