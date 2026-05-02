# views

这里是前端页面级视图。

## 文件说明

- `DashboardView.js`: 概览页
- `DisksView.js`: 磁盘与分区
- `PoolsView.js`: 池、拓扑与属性
- `DatasetsView.js`: 数据集

## 当前页面能力

- Dashboard 显示后端提供的 `summary`
- Disks 页面支持展开分区，并显示池归属
- Pools 页面支持展开拓扑，详情抽屉按只读/可编辑属性分组展示
- Pools 详情页支持编辑可写属性、保存前确认、逐项结果回显，以及修改后的主动刷新
- Datasets 页面直接消费后端整理结果
