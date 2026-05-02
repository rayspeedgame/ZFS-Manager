# views

这里是前端页面级视图。

## 文件说明

- `DashboardView.js`: 概览页
- `DisksView.js`: 磁盘与分区
- `PoolsView.js`: 池、拓扑与属性
- `DatasetsView.js`: 数据集

## 当前页面能力

- Dashboard 显示后端提供的 `summary`
- Disks 页支持展开分区，并显示池归属
- Pools 页支持展开拓扑，抽屉按只读/可编辑属性分组，且只读属性支持高级展开
- Datasets 页直接消费后端整理结果
