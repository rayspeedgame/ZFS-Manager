# views

路由级页面组件。

## Files

- `DashboardView.vue`: 总览页
- `DisksView.vue`: 磁盘与分区页
- `PoolsView.vue`: pool 页面容器，负责列表、抽屉、对话框和拓扑流程
- `DatasetsView.vue`: dataset 页面容器，负责树视图、抽屉、对话框和创建销毁流程
- `SettingsView.vue`: 后端设置页，负责配置加载、保存、重载和 SSH 测试

## Notes

- `Dashboard` 渲染后端汇总数据
- `Disks` 支持分区展开和 pool 归属展示
- `Pools` 将大部分渲染委托给 `components/pools/`
- `Datasets` 将大部分渲染委托给 `components/datasets/`
- `Settings` 负责后端连接参数、轮询参数和网页登录设置
