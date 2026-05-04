# router

> [English Version](./README.md)

前端路由配置。

## Files

- `index.js`: 使用 `createWebHashHistory()` 创建 router
- `routes.js`: `Dashboard`、`Disks`、`Pools`、`Datasets`、`Settings` 的路由元数据

## Notes

- 路由仍然使用 hash history，这样直接刷新不需要后端额外提供 SPA fallback
- 路由元数据使用 `labelKey` 和 `descriptionKey`，方便语言切换时自动刷新文案
