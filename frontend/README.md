# Frontend

> [中文版](./README.zh-CN.md)

The frontend uses Vue 3, routed views, shared dialogs, and i18n to present the storage UI, task records, and recurring workflows.

## Current Responsibilities

- Render pool, dataset, snapshot, task, and schedule pages
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
