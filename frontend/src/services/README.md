# services

> [中文版本](./README.zh-CN.md)

Frontend API service layer.

## Files

- `api.js`
  - Pool and dataset create, destroy, property, and maintenance requests
  - Snapshot list/filter/detail, create, delete, and rollback
  - `scrub` start/stop plus replace, RAID-Z expansion, and auxiliary topology updates
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
- Snapshot reads support search, filtering, sorting, and pagination parameters
- The single-disk SMART refresh endpoint currently causes the backend to refresh the complete state
- Development defaults to port `8000` on the current host; `VITE_BACKEND_ORIGIN` or `VITE_BACKEND_PORT` can override it
