# views

> [English Version](./README.md)

路由级页面组件。

## 文件

- `DashboardView.vue`：总览页
- `DisksView.vue`：磁盘与分区页
- `PoolsView.vue`：pool 页面容器，负责列表、抽屉、对话框、拓扑和 `scrub` 流程
- `DatasetsView.vue`：dataset 页面容器，负责树视图、抽屉、对话框和创建/销毁流程
- `SchedulesView.vue`：计划任务页面，负责按周 `scrub` 规则以及未来定时快照入口
- `TasksView.vue`：任务记录和状态页面，支持分页、筛选和详情侧内容
- `SettingsView.vue`：后端设置页，负责配置加载、保存、重载和 SSH 测试

## 说明

- `Dashboard` 渲染后端摘要数据
- `Disks` 支持分区展开和 pool 归属展示
- `Pools` 将大部分渲染委托给 `components/pools/`
- `Datasets` 将大部分渲染委托给 `components/datasets/`
- `Schedules` 是第一个专门承载周期工作流的页面
- `Tasks` 在当前筛选没有结果时仍会保留筛选控件和页面框架
- `Settings` 负责后端连接参数、轮询参数和网页登录设置
