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

- `GET /api/state`
  - returns the unified state snapshot
- `POST /api/state/refresh`
  - forces a refresh
- `GET /api/tasks`
  - supports pagination and status filtering
- `PUT /api/disks/{disk_key}/label`
  - persists custom disk labels
- `GET /api/disks/{disk_key}/smart`
  - returns cached SMART data for a specific disk
- `POST /api/disks/{disk_key}/smart/refresh`
  - forces full SMART refresh and returns updated data
- `POST /api/pools/{pool_name}/offline`
- `POST /api/pools/{pool_name}/online`
- `POST /api/pools/{pool_name}/clear`
- `POST /api/pools/{pool_name}/replace`
- `POST /api/pools/{pool_name}/raidz-expand`

## Current Rules

- new-device flows should resolve to `commandPath` when possible
- existing pool-member maintenance must resolve to `commandTarget`
- validators accept aliases such as `displayName`, `kernelPath`, `byIdPath`, and stored `aliases`
- the backend still resolves back to the correct current execution target before running the command

## Maintenance Notes

- `scrub`, `replace/resilver`, and RAID-Z `expansion` are long-running flows tracked by the task system
- RAID-Z `expansion` is implemented as vdev-level `zpool attach`, not single-disk `online -e`
- write routes still force one immediate refresh so the recovery layer can take over progress tracking quickly
