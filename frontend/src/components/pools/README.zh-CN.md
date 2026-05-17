# components/pools

> [English Version](./README.md)

池专用工作流组件。

## 文件

- `PoolListPanel.vue`：池清单列表和入口操作
- `PoolDetailDrawer.vue`：池信息、可编辑属性以及 `scrub` 状态/操作
- `PoolTopologyDrawer.vue`：拓扑添加/移除工作流
- `CreatePoolDrawer.vue`：分步池创建 UI
- `PoolActionDialogs.vue`：池写操作的确认和结果对话框
- `TopologyNode.vue`：递归拓扑展示
- `pool-form-config.js`：池属性字段、拓扑选项和创建池配置

## 说明

- 这些组件负责渲染 UI 并向上发出事件
- `PoolDetailDrawer.vue` 现在包含独立的 `scrub` 区块，展示：
  - 状态摘要
  - 进度和 ETA
  - 开始与停止按钮
- `PoolsView.vue` 仍然拥有 API 调用、实时快照重绑定和草稿安全控制
