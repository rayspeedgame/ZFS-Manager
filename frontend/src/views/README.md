# views

这里是前端页面级视图。

## 文件说明

- `DashboardView.js`: 概览页
- `DisksView.js`: 磁盘与分区
- `PoolsView.js`: 池、拓扑与属性
- `DatasetsView.js`: dataset / zvol / snapshot inventory

## 当前页面能力

- Dashboard 显示后端提供的 `summary`
- Disks 支持展开分区，并显示 pool 归属
- Pools 支持属性编辑、topology 变更、新建、删除、remove
- Datasets 支持树形 inventory、可选显示 snapshot、属性编辑、创建和删除
