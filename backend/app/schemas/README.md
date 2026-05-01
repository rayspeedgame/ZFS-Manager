# backend/app/schemas

This folder contains Pydantic models used by the backend.

## Files

- [zfs_state.py](./zfs_state.py)
  - models the application snapshot returned by REST and WebSocket

## Current snapshot design

The snapshot is now split into:

- `meta`
  - app status
  - source status
  - timestamps
  - stale age
  - section state
  - refresh plan
- `data`
  - summary metrics
  - UI-ready `disks`, `pools`, and `datasets`
  - raw overview data retained for compatibility and debugging

Computed compatibility fields such as `status` and `disk_overview` are still
present so older consumers do not break while the frontend evolves.
