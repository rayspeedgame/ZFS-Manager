# stores

> [中文版本](./README.zh-CN.md)

Pinia stores live here.

## Files

- `app.js`
  - WebSocket lifecycle
  - Snapshot cache
  - Auth state
  - Login, logout, refresh actions

## Notes

- This store replaces the old module singleton state implementation
- When login gate is enabled, the store establishes WebSocket connection after auth succeeds
