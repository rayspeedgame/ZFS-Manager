# stores

> [中文版本](./README.zh-CN.md)

Pinia stores live here.

## Files

- `app.js`
  - WebSocket lifecycle
  - Snapshot cache
  - Auth state
  - Login, logout, and refresh actions
- `tasks.js`
  - Task records cache
  - Selected task detail
  - Pagination state
  - Status filter state
  - Periodic refresh logic

## Notes

- These stores replace the older singleton-style frontend state
- When login is enabled, the app store establishes WebSocket only after auth succeeds
- The tasks store is now responsible for keeping task-page UX state stable across refreshes
