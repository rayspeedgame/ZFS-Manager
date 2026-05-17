# Project Directory Structure

> [中文版本](./ProjectDirectoryStructure.zh-CN.md)

```text
ZFS-Manager/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- ssh/
|   |-- config/
|   |   |-- config.example.json
|   |   |-- config.json
|   |   `-- tasks.sqlite3
|   |-- scripts/
|   |-- tests/
|   |   `-- fixtures/
|   |-- README.md
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- app/
|   |   |   |-- common/
|   |   |   |-- datasets/
|   |   |   `-- pools/
|   |   |-- i18n/
|   |   |   `-- messages/
|   |   |       |-- en-US/
|   |   |       `-- zh-CN/
|   |   |-- lib/
|   |   |-- router/
|   |   |-- services/
|   |   |-- store/
|   |   |-- stores/
|   |   `-- views/
|   |-- README.md
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- Documents/
|   |-- README.md
|   |-- agent.md
|   |-- target.md
|   |-- Roadmap.md
|   |-- TaskSystemArchitecture.md
|   |-- ProjectStruction.md
|   `-- ProjectDirectoryStructure.md
`-- README.md
```

## Frontend Hotspots

- `frontend/src/views/TasksView.vue`
  - Task records and status page
  - Paged task browsing, status filtering, refresh, and task detail drill-down
- `frontend/src/views/SchedulesView.vue`
  - Schedule page for recurring workflows
  - Currently owns scheduled `scrub` creation and the snapshot placeholder panel
- `frontend/src/views/PoolsView.vue`
  - Pool overview, topology, property editing, and `scrub` actions
- `frontend/src/components/pools/PoolDetailDrawer.vue`
  - Pool detail drawer with `scrub` summary, start/stop controls, and property editing
- `frontend/src/stores/tasks.js`
  - Task list cache, pagination state, status filter, selection, and auto-refresh
- `frontend/src/services/api.js`
  - Pool and dataset writes, task APIs, task schedule APIs, auth APIs, and `scrub` APIs
- `frontend/src/router/routes.js`
  - Navigation metadata for dashboard, disks, pools, datasets, schedules, task records, and settings

## Backend Hotspots

- `backend/config/tasks.sqlite3`
  - SQLite database for tasks and task schedules
- `backend/app/core/config.py`
  - Configuration loading, saving, and task database path resolution
- `backend/app/services/task_store.py`
  - SQLite-backed persistence for tasks and schedules
- `backend/app/services/task_manager.py`
  - In-memory runtime task manager with pagination and filtering support
- `backend/app/services/task_recovery.py`
  - Recovery registry and active-task reconciliation
- `backend/app/services/task_scheduler.py`
  - Background scheduler for recurring workflows
- `backend/app/services/pool_scrubber.py`
  - `zpool scrub` / `zpool scrub -s` executor
- `backend/app/schemas/pool_scrub.py`
  - `scrub` request-response shape
- `backend/app/schemas/task_schedule.py`
  - Schedule create, update, list, and detail models
- `backend/app/api/rest.py`
  - State, settings, auth, task list/detail, task schedules, and `scrub` start/stop endpoints
- `backend/app/services/poller.py`
  - Generates structured `scanStatus` for each pool

## Related Change Clusters

- Task system
  - `backend/app/services/task_store.py`
  - `backend/app/services/task_manager.py`
  - `backend/app/services/task_recovery.py`
  - `backend/app/schemas/task.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
- Scheduled workflows
  - `backend/app/services/task_scheduler.py`
  - `backend/app/schemas/task_schedule.py`
  - `backend/app/api/rest.py`
  - `frontend/src/views/SchedulesView.vue`
- Scrub
  - `backend/app/services/pool_scrubber.py`
  - `backend/app/schemas/pool_scrub.py`
  - `backend/app/api/rest.py`
  - `backend/app/services/poller.py`
  - `frontend/src/views/PoolsView.vue`
  - `frontend/src/components/pools/PoolDetailDrawer.vue`
- Configuration and auth
  - `backend/app/core/config.py`
  - `backend/app/core/auth.py`
  - `backend/app/main.py`
