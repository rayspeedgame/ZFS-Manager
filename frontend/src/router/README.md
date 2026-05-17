# router

> [中文版本](./README.zh-CN.md)

Frontend routing configuration.

## Files

- `index.js`: Creates the router with `createWebHashHistory()`
- `routes.js`: Route metadata for `Dashboard`, `Disks`, `Pools`, `Datasets`, `Schedules`, `Tasks`, and `Settings`

## Notes

- Hash history remains in use so direct refresh does not require backend SPA fallback
- Route metadata uses `labelKey` and `descriptionKey` so navigation text updates on locale switch
- The tasks route is presented as task records and status, while schedules is a separate top-level workflow page
