# components/pools

> [English Version](./README.md)

池专用工作流组件。

## Files

- `PoolListPanel.vue`: 池清单列表和入口操作
- `PoolDetailDrawer.vue`: 只读信息加上可编辑的池属性
- `PoolTopologyDrawer.vue`: 拓扑添加/移除工作流
- `CreatePoolDrawer.vue`: 分步池创建 UI
- `PoolActionDialogs.vue`: 池写操作的确认和结果对话框
- `TopologyNode.vue`: 递归拓扑展示
- `pool-form-config.js`: 池属性字段、拓扑选项和创建池配置

## Notes

- 这些组件仅渲染 UI 并向上发送事件
- `PoolsView.vue` 拥有 API 调用、实时快照重新绑定和草稿安全
