# views

> [English Version](./README.md)

路由级页面组件。

## 文件

- `DashboardView.vue`：总览页
- `DisksView.vue`：磁盘与分区页面
- `PoolsView.vue`：存储池页面容器
- `DatasetsView.vue`：数据集页面容器，包含手动快照快速创建入口
- `SnapshotsView.vue`：独立快照管理页面
- `SchedulesView.vue`：定时 `scrub` 与定时 `snapshot` 页面
- `TasksView.vue`：任务记录与状态页面
- `SettingsView.vue`：后端设置页面

## 说明

- `SchedulesView` 现在支持从分钟级到月级的快照计划
- 删除计划任务已经改成和其他危险操作一致的站内确认弹窗
- `SnapshotsView` 继续作为快照集中管理界面
