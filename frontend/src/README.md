# src

> [中文版本](./README.zh-CN.md)

`src/` contains the Vue frontend source code.

## Structure

- `App.vue`: Root application shell and login gate toggle
- `main.js`: Application entry point
- `i18n/`: Locale initialization and translation resources
- `styles.css`: Global shared styles
- `components/`: Reusable UI components
- `lib/`: Formatting helpers
- `router/`: Router creation and route metadata
- `services/`: REST API calls
- `store/`: Compatibility adapter layer
- `stores/`: Pinia stores
- `views/`: Route-level page containers

## Current Notes

- `PoolsView.vue` and `DatasetsView.vue` remain page containers for API calls, live snapshot rebinding, and draft protection
- `SnapshotsView.vue` owns snapshot filtering, sorting, creation, deletion, and rollback
- `TasksView.vue` owns task-record browsing, status filtering, pagination, and detail loading
- `SchedulesView.vue` owns snapshot schedules from minutely through monthly, weekly scrub schedules, and schedule create/toggle/delete actions
- `DisksView.vue` includes inline SMART health column in the disk table and a full SMART attribute dialog via `ConfirmDialog`
- `SettingsView.vue` handles settings read, save, SSH test, login configuration editing, and SMART poller intervals
- `i18n/messages.js` is only an aggregation entry point; actual translation resources live in `i18n/messages/<locale>/<module>.js`
- Route definitions still expose translation keys so sidebar and titles refresh immediately on locale changes
- The schedule backend supports partial updates, but the current page does not yet provide a complete edit form
