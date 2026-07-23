# store

> [中文版本](./README.zh-CN.md)

Compatibility adapter layer.

## Files

- `state.js`
  - Exposes historical `useAppState()` interface
  - Internally delegates to new Pinia store and API service
  - Re-exports `getDiskSmartData` and `refreshDiskSmartData` from the API service layer

## Notes

- Transport layer connection state remains independent of backend data source state in `snapshot.meta`
- New code should directly use `src/stores/app.js` and `src/services/api.js`
