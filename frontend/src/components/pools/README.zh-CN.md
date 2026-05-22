# components/pools

> [English Version](./README.md)

这里放 pool 相关的页面组件。

## 主要文件

- `PoolListPanel.vue`
  - pool 列表和入口操作
- `PoolDetailDrawer.vue`
  - pool 详情、属性、`scrub`、`clear`
- `PoolTopologyDrawer.vue`
  - 拓扑编辑、设备维护、replace、RAID-Z expansion
- `CreatePoolDrawer.vue`
  - 分步骤创建 pool
- `PoolActionDialogs.vue`
  - pool 写操作的统一确认和结果弹窗
- `TopologyNode.vue`
  - 递归拓扑展示
- `pool-form-config.js`
  - pool 属性、拓扑选项和创建配置

## 当前约定

- 这些组件主要负责展示和向上派发事件
- `PoolDetailDrawer.vue` 负责池级维护摘要
- `PoolTopologyDrawer.vue` 负责设备级与 vdev 级维护入口

### 拓扑显示字段

拓扑组件会同时使用三类字段：

- 显示字段
  - `displayLabel`
- 辅助识别字段
  - `kernelPath`
  - `byIdPath`
  - `aliases`
- 执行字段
  - `commandTarget`

### 当前已承载的维护动作

- `offline / online`
- `replace`
- RAID-Z `expansion`

其中 RAID-Z `expansion` 的按钮挂在 vdev 条目，而不是叶子磁盘条目。
