# services

> [中文版本](./README.zh-CN.md)

Frontend API service layer.

## Files

- `api.js`
  - pool, dataset write requests
  - Settings read, save, SSH test
  - Login status, login, logout
  - Shared API base address helper

## Notes

- All requests carry `credentials: "include"` by default to reuse backend login cookie
- This layer is responsible for aligning request paths and payload shapes with backend API
