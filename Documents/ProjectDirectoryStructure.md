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
|   |   `-- config.json
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
|   |-- ProjectStruction.md
|   `-- ProjectDirectoryStructure.md
`-- README.md
```

## Frontend Notes

- `frontend/src/views/TasksView.vue`
  - Dedicated task page for recent write workflows, progress, and command logs
- `frontend/src/stores/tasks.js`
  - Task list loading, selected task loading, and periodic refresh
- `frontend/src/views/SettingsView.vue`
  - Backend settings page, handles loading, editing, saving, reloading, and SSH testing
- `frontend/src/components/app/AppLoginGate.vue`
  - Web password login interface
- `frontend/src/App.vue`
  - Decides whether to show login page or main application shell based on login status
- `frontend/src/i18n/messages/`
  - Translation resources are split by language and module
  - Each language now includes `app`, `routes`, `common`, `dashboard`, `disks`, `pools`, `datasets`, `tasks`, `settings`, `properties`, and `login`

## Backend Notes

- `backend/config/`
  - Current active configuration directory
- `backend/app/core/config.py`
  - Configuration loading, saving, path resolution, and environment variable overrides
- `backend/app/core/auth.py`
  - Lightweight login state handling
- `backend/app/api/rest.py`
  - State endpoints, settings endpoints, auth endpoints, ZFS write endpoints, and task endpoints
- `backend/app/services/task_manager.py`
  - In-memory task registry used to track recent write workflows
- `backend/app/schemas/task.py`
  - Task records, command logs, and task list/detail response models
- `backend/app/main.py`
  - Application startup, CORS, and auth middleware

## Related Hotspots

- Configuration & Auth
  - `backend/app/core/config.py`
  - `backend/app/core/auth.py`
  - `backend/app/api/rest.py`
  - `backend/app/main.py`
- Task System
  - `backend/app/services/task_manager.py`
  - `backend/app/schemas/task.py`
  - `backend/app/api/rest.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
- Frontend State & Login Gate
  - `frontend/src/stores/app.js`
  - `frontend/src/store/state.js`
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppLoginGate.vue`
- Frontend i18n
  - `frontend/src/i18n/index.js`
  - `frontend/src/i18n/messages.js`
  - `frontend/src/i18n/messages/en-US/`
  - `frontend/src/i18n/messages/zh-CN/`
