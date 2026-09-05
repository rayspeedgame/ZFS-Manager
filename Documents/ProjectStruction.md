# Project Structure

> [中文版本](./ProjectStruction.zh-CN.md)

## Backend

- `app/api`
  - REST and WebSocket endpoints
- `app/core`
  - configuration, authentication, client tracking, and shared state
- `app/schemas`
  - request and response models
- `app/services`
  - ZFS orchestration, refresh, task persistence/recovery, and scheduling
- `app/ssh`
  - SSH command execution and parser helpers

## Frontend

- `components/app`
  - application shell components such as the sidebar, topbar, refresh action, and locale switcher
- `components/common`
  - shared UI primitives for drawers, dialogs, property lists, command results, and logs
- `components/pools`
  - pool-only workflow components and configuration
- `components/datasets`
  - dataset-only workflow components and configuration
- `i18n`
  - locale bootstrap, browser locale detection, local storage persistence, and translation message bundles
- `router`
  - route definitions and router bootstrap; route metadata now uses translation keys
- `stores`
  - Pinia store that owns snapshot lifecycle and WebSocket state
- `services`
  - REST queries and write requests
- `store`
  - compatibility adapter that still exposes `useAppState()`
- `views`
  - routed page containers that assemble the smaller workflow components

## Data Flow

1. The backend polls or refreshes ZFS state and normalizes it into a snapshot.
2. The frontend store receives that snapshot over WebSocket or on-demand refresh.
3. Routed views derive page-specific state from the snapshot.
4. Child components render the UI and emit events upward.
5. Routed views call the REST layer for queries or writes; writes create tasks, execute SSH commands, and force a backend state refresh.
6. Long-running tasks are reconciled against later ZFS state, while schedules persist in SQLite and are fired by the scheduler.

## Runtime and Persistence

- `backend/app/runtime.py` assembles long-lived services and rebuilds them after configuration saves.
- State snapshots live in memory; tasks and schedules live in SQLite; application settings and disk labels live in JSON configuration.
- `docker-compose.yml` and `Dockerfile` provide container entry points. SSH mode connects to a real ZFS host, while fixture mode is intended for read-only UI demonstrations.

## Frontend Refactor Outcome

- Large pool and dataset pages were split into smaller workflow components.
- Property-heavy UIs now share `PropertySection.vue` and `PropertyFieldList.vue`.
- Confirmation results and SSH logs now share dedicated common components.
- Dirty-draft guards prevent live snapshot updates from wiping active user input.
- Locale changes are handled centrally and should update shell navigation plus page-level workflow copy immediately.
