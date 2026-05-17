# api

> [中文版本](./README.zh-CN.md)

This layer exposes the latest in-memory snapshot and control endpoints to the frontend.

## File Descriptions

- `rest.py`: HTTP endpoints for state reads, settings, auth, writes, task records, and schedules
- `ws.py`: WebSocket push for frontend real-time updates

## Current API Conventions

- `GET /api/state`: Return the complete application snapshot
- `POST /api/state/refresh`: Trigger a full backend refresh
- `GET /api/settings`: Read active configuration
- `PUT /api/settings`: Save configuration and hot-reload runtime
- `POST /api/settings/test-ssh`: Test SSH connectivity without saving settings
- `GET /api/auth/status`: Return whether login is enabled and whether the request is authenticated
- `POST /api/auth/login`: Login
- `POST /api/auth/logout`: Logout
- `GET /api/tasks`: List task records
  - supports `page`, `page_size`, and `status_filter`
- `GET /api/tasks/{task_id}`: Return one task detail
- `GET /api/task-schedules`: List recurring schedules
- `POST /api/task-schedules`: Create a recurring schedule
- `PATCH /api/task-schedules/{schedule_id}`: Update a recurring schedule
- `DELETE /api/task-schedules/{schedule_id}`: Delete a recurring schedule
- `POST /api/pools/{pool_name}/scrub/start`: Start pool scrub
- `POST /api/pools/{pool_name}/scrub/stop`: Stop pool scrub
- `POST /api/pools/{pool_name}/properties`: Modify pool properties
- `POST /api/pools/{pool_name}/topology`: Add topology devices
- `POST /api/pools`: Create pool
- `POST /api/pools/{pool_name}/destroy`: Delete pool
- `POST /api/pools/{pool_name}/remove`: Remove removable topology targets
- `POST /api/datasets`: Create dataset / zvol
- `POST /api/datasets/{dataset_name:path}/properties`: Modify dataset properties
- `POST /api/datasets/{dataset_name:path}/destroy`: Delete dataset

## Current Constraints

- Dataset routes use `{dataset_name:path}` so multi-level names like `tank/data` work
- All `/api/*` requests except public endpoints still pass through auth middleware
- `OPTIONS` preflight is allowed so credentialed browser requests can complete correctly
- Write operations actively refresh after completion to push real host state back to the frontend quickly
