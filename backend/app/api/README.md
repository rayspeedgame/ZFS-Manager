# api

> [中文版](./README.zh-CN.md)

This layer exposes HTTP and WebSocket endpoints to the frontend. It now uses
resource-oriented route modules instead of one oversized REST file, while
keeping `app.api.rest` as the stable aggregation entrypoint used by
`app.main`.

## Files

- `rest.py`: aggregates all HTTP routers into one stable import target
- `ws.py`: WebSocket endpoint for real-time frontend updates
- `common.py`: shared task-message and command-log helpers used by write routes
- `constants.py`: API-side dataset property allowlists used during validation
- `validators.py`: shared REST validation and lookup helpers
- `routes/system.py`: state, auth, settings, SSH test, and health endpoints
- `routes/tasks.py`: task records and recurring schedule endpoints
- `routes/pools.py`: pool create/destroy/remove/properties/topology/scrub endpoints
- `routes/datasets.py`: dataset create/destroy/property endpoints
- `routes/snapshots.py`: snapshot list/filter/detail/create/delete/rollback endpoints

## Current Conventions

- `GET /api/state`: return the complete application snapshot
- `POST /api/state/refresh`: trigger a full backend refresh
- `GET /api/auth/status`: return whether login is enabled and whether the request is authenticated
- `POST /api/auth/login`: login
- `POST /api/auth/logout`: logout
- `GET /api/settings`: read active configuration
- `PUT /api/settings`: save configuration and hot-reload runtime
- `POST /api/settings/test-ssh`: test SSH connectivity without saving settings
- `GET /api/tasks`: list task records
  - supports `page`, `page_size`, and `status_filter`
- `GET /api/tasks/{task_id}`: return one task detail
- `GET /api/task-schedules`: list recurring schedules
- `POST /api/task-schedules`: create a recurring schedule
- `PATCH /api/task-schedules/{schedule_id}`: update a recurring schedule
- `DELETE /api/task-schedules/{schedule_id}`: delete a recurring schedule
- `POST /api/pools`: create pool
- `POST /api/pools/{pool_name}/destroy`: destroy pool
- `POST /api/pools/{pool_name}/remove`: remove a removable topology target
- `POST /api/pools/{pool_name}/properties`: modify pool properties
- `POST /api/pools/{pool_name}/topology`: add supported topology devices
- `POST /api/pools/{pool_name}/scrub/start`: start pool scrub
- `POST /api/pools/{pool_name}/scrub/stop`: stop pool scrub
- `POST /api/datasets`: create dataset or zvol
- `POST /api/datasets/{dataset_name:path}/destroy`: destroy dataset
- `POST /api/datasets/{dataset_name:path}/properties`: modify dataset properties
- `GET /api/snapshots`: list snapshots with pagination and filtering
- `GET /api/snapshots/filters`: list snapshot filter values
- `GET /api/snapshots/{snapshot_name:path}`: return one snapshot detail
- `GET /api/datasets/{dataset_name:path}/snapshots`: return recent snapshots for one dataset
- `POST /api/datasets/{dataset_name:path}/snapshots`: create a snapshot
- `DELETE /api/snapshots/{snapshot_name:path}`: delete a snapshot
- `POST /api/snapshots/{snapshot_name:path}/rollback`: rollback a snapshot

## Design Notes

- Dataset and snapshot names use `{name:path}` parameters so nested names like
  `tank/data` and `tank/data@snap-1` work correctly.
- All `/api/*` requests except public bootstrap endpoints still pass through
  auth middleware in `app.main`.
- `OPTIONS` preflight is intentionally allowed so browser credentialed requests
  can complete without false `401` failures.
- Write routes still force a refresh after command execution so the frontend
  sees real host state instead of local assumptions.
- Long-running pool-side work such as scrub is handed back to the task recovery
  layer after the initial command succeeds.
