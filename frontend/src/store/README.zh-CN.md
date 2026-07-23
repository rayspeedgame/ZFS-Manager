# store

> [English Version](./README.md)

兼容适配层。

## Files

- `state.js`
  - 暴露历史上的 `useAppState()` 接口
  - 内部委托给新的 Pinia store 和 API service
  - 重新导出 `getDiskSmartData` 和 `refreshDiskSmartData` 来自 API 服务层

## Notes

- 传输层连接状态仍然独立于 `snapshot.meta` 中的后端数据源状态
- 新代码优先直接使用 `src/stores/app.js` 与 `src/services/api.js`
