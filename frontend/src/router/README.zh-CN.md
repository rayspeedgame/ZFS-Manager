# router

> [English Version](./README.md)

前端路由配置。

## 文件

- `index.js`：使用 `createWebHashHistory()` 创建 router
- `routes.js`：`Dashboard`、`Disks`、`Pools`、`Datasets`、`Snapshots`、`Schedules`、`Tasks` 和 `Settings` 的路由元数据

## 说明

- 路由仍然使用 hash history，这样直接刷新不需要后端额外提供 SPA fallback
- 路由元数据使用 `labelKey` 和 `descriptionKey`，方便语言切换时自动刷新文案
- 任务路由现在以“任务记录和状态”呈现，计划任务则是独立的一级页面
