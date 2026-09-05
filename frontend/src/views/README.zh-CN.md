# views

> [English Version](./README.md)

这里放路由级页面组件。

## 主要页面

- `DashboardView.vue`
  - 总览页
- `DisksView.vue`
  - 磁盘与分区页
- `PoolsView.vue`
  - pool 页面容器
- `DatasetsView.vue`
  - dataset 页面容器，包含快速手动快照入口
- `SnapshotsView.vue`
  - 独立快照管理页
- `SchedulesView.vue`
  - 定时 `scrub` 和定时 `snapshot`
- `TasksView.vue`
  - 任务记录和状态页
- `SettingsView.vue`
  - 后端设置页

## 当前说明

### `DisksView`

- 使用规范化后的磁盘身份模型
- 主标题来自 `displayName`
- 副信息展示 `kernelPath` 和 `byIdPath`
- 自定义名称通过 `diskKey` 持久化
- 磁盘表内置 SMART 健康列（PASS/FAIL 徽标 + 温度），数据来自 WebSocket 快照的 `smart_overview`
- 完整 SMART 详情通过 `ConfirmDialog`（result 模式）弹窗展示，包含温度、通电时间、协议、序列号、固件和可滚动的属性表
- 详情中的手动刷新当前会请求后端完整刷新所有状态，而不是只轮询所选磁盘

### `PoolsView`

- 新设备相关操作优先使用 `commandPath`
- 已在 pool 内的成员维护使用 `commandTarget`
- 拓扑显示优先使用别名，不直接暴露原始命令标识
- 现在已经承载：
  - `scrub`
  - `clear`
  - `offline / online`
  - `replace`
  - RAID-Z `expansion`
- 现有 pool 的拓扑更新只允许添加辅助 vdev，不支持添加新的 data vdev

### `SnapshotsView`

- 支持搜索、pool/dataset/类型筛选、分页和排序
- 支持查看详情、创建、删除和安全/强制模式回滚，操作可用性由后端能力标记决定

### `SchedulesView`

- 支持从分钟到月的快照计划
- 支持定时 `scrub`
- `scrub` 当前只支持每周频率；计划可创建、启停和删除，完整编辑表单尚未实现

### `TasksView`

- 支持分页、状态筛选和自动刷新
- 长任务详情会展示命令日志
- RAID-Z expansion 任务会经过：
  - `expand` 阶段
  - 自动 `scrub` 阶段

### `SettingsView`

- 读取并保存 SSH、轮询、登录和磁盘标签配置
- 提供 SSH 连接测试，并可分别调整活跃/空闲 SMART 轮询间隔
