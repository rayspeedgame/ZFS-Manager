# services

> [中文版本](./README.zh-CN.md)

Frontend API service layer.

## Files

- `api.js`
  - Pool and dataset write requests
  - `scrub` start and stop
  - Task records list and detail
  - Task schedules list, create, update, and delete
  - Settings read, save, and SSH test
  - Disk SMART data retrieval (`getDiskSmartData`) and refresh (`refreshDiskSmartData`)
  - Login status, login, and logout
  - Shared API base-address helper

## Notes

- All requests carry `credentials: "include"` by default so the backend login cookie is reused
- This layer aligns request paths and payload shapes with backend API expectations
- Task record reads now support pagination and status filtering parameters
