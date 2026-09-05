# api

> [中文版本](./README.zh-CN.md)

This directory holds the backend HTTP API layer. `rest.py` now acts as the stable aggregation entry point while implementation lives under `routes/`.

## Structure

- `rest.py`
  - router aggregation entry point
- `ws.py`
  - WebSocket state push
- `common.py`
  - shared task-message and command-log helpers
- `constants.py`
  - API-boundary constants and property allow-lists
- `validators.py`
  - request validation and current-snapshot resolution helpers
- `routes/system.py`
  - system state, auth, and settings
- `routes/tasks.py`
  - tasks and schedules
- `routes/disks.py`
  - disk labels, SMART data retrieval
- `routes/pools.py`
  - pools, maintenance actions, replace, and RAID-Z expansion
- `routes/datasets.py`
  - datasets
- `routes/snapshots.py`
  - snapshots

## Current API Surface

- State and settings: `GET /api/state`, `POST /api/state/refresh`, `GET /api/health`, `GET/PUT /api/settings`, and `POST /api/settings/test-ssh`
- Authentication: `GET /api/auth/status`, `POST /api/auth/login`, and `POST /api/auth/logout`
- Disks: `PUT /api/disks/{disk_key}/label`, `GET /api/disks/{disk_key}/smart`, and `POST /api/disks/{disk_key}/smart/refresh`
- Pools: create, destroy, remove device, update properties, start/stop scrub, offline/online/replace devices, RAID-Z expansion, clear errors, and update topology
- Datasets: create, destroy, and update properties; `{dataset_name:path}` accepts names containing `/`
- Snapshots: paginated list, filter values, detail, per-dataset list, create, delete, and rollback; `{snapshot_name:path}` accepts names containing `/`
- Tasks: task list/detail plus schedule list, create, partial update, and delete
- Live state: `WS /ws/state`

The snapshot list supports `search`, `pool`, `dataset`, `snapshot_type`, `sort_by`, `sort_order`, `page`, and `page_size`.

## Current Rules

- new-device flows should resolve to `commandPath` when possible
- existing pool-member maintenance must resolve to `commandTarget`
- validators accept aliases such as `displayName`, `kernelPath`, `byIdPath`, and stored `aliases`
- the backend still resolves back to the correct current execution target before running the command
- existing-pool topology updates currently accept only `log`, `cache`, `spare`, `special`, and `dedup`; adding a new data vdev is rejected
- all ZFS-mutating writes and schedule execution require `poller.mode=ssh`; settings, authentication, and disk-label writes do not
- a manual refresh initiated through a single-disk SMART endpoint currently calls `refresh_once(force_all=True)`, refreshing the complete state rather than only that disk

## Maintenance Notes

- `scrub`, `replace/resilver`, and RAID-Z `expansion` are long-running flows tracked by the task system
- RAID-Z `expansion` is implemented as vdev-level `zpool attach`, not single-disk `online -e`
- write routes still force one immediate refresh so the recovery layer can take over progress tracking quickly
