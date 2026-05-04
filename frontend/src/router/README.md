# router

> [中文版本](./README.zh-CN.md)

Frontend routing configuration.

## Files

- `index.js`: Creates router using `createWebHashHistory()`
- `routes.js`: Route metadata for `Dashboard`, `Disks`, `Pools`, `Datasets`, `Settings`

## Notes

- Routes still use hash history so direct refresh doesn't require backend SPA fallback
- Route metadata uses `labelKey` and `descriptionKey` for automatic text refresh on language switch
