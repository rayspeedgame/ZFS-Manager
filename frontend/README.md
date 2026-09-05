# Frontend

> [中文版](./README.zh-CN.md)

The frontend uses Vue 3, routed views, shared dialogs, and i18n to present the storage UI, task records, and recurring workflows.

## Current Responsibilities

- Render eight routed views: Dashboard, disks, pools, datasets, snapshots, schedules, tasks, and settings
- Receive the unified state snapshot over WebSocket and use REST for queries and writes
- Support custom disk labels, SMART detail, settings editing, SSH testing, and the optional login gate
- Keep recurring workflow interactions consistent with the rest of the app
- Present destructive actions through shared confirmation dialogs
- Route all user-visible copy through i18n

## Important Current Views

- `SnapshotsView`: centralized snapshot management
- `SchedulesView`: recurring `scrub` and recurring `snapshot`
- `TasksView`: task records and status
- `DatasetsView`: quick manual snapshot initiation
- `SettingsView`: poller configuration with separate active and idle interval controls

## Current Schedule UX

- `scrub` and `snapshot` live on the same schedules page
- Snapshot schedules support:
  - minutely
  - hourly
  - daily
  - weekly
  - monthly
- The page now uses shared in-app confirmation dialogs for deleting schedules instead of browser-native dialogs
- Scrub schedules currently support weekly frequency only
- The page supports schedule create, enable/disable, and delete; the backend supports partial updates, but there is not yet a complete edit form

## Local Development Configuration

- Development defaults to port `8000` on the current host; production defaults to the same origin
- `VITE_BACKEND_ORIGIN` selects a complete backend origin, while `VITE_BACKEND_PORT` overrides only the port
- `VITE_SHOW_JSON_DEBUG=true` exposes the Dashboard JSON debug panel
