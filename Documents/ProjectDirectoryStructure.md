# Project Directory Structure

> [中文版](./ProjectDirectoryStructure.zh-CN.md)

## Backend Hotspots

- `backend/app/core/client_tracker.py`
  - Tracks connected WebSocket client count
  - Drives active↔idle poller mode switching in ≤1 second
- `backend/app/services/poller.py`
  - State collection with client-aware active/idle refresh cadences
  - Mode detection runs at fixed 1-second interval; configurable tick only gates refresh frequency
  - Five independent job schedules (disks, pools, datasets, properties, smart), each with separate active and idle intervals
  - Non-physical disk filtering (`loop`, `ram`, `fd`, `sr`, `zd`, `zram` excluded)
- `backend/app/services/task_scheduler.py`
  - Recurring workflow scheduler
  - Executes scheduled `scrub`
  - Executes scheduled `snapshot`
  - Coordinates schedule-scoped snapshot retention cleanup
- `backend/app/services/snapshot_metadata.py`
  - Defines the ZFS user-property keys used to tag scheduled snapshots
- `backend/app/services/snapshot_retention.py`
  - Builds short scheduled snapshot names
  - Groups schedule-owned snapshots per dataset for keep-latest cleanup
- `backend/app/services/snapshot_creator.py`
  - Writes scheduled snapshot user properties through `zfs snapshot -o`
- `backend/app/services/snapshot_query.py`
  - Reads schedule ownership fields back from snapshot properties
- `backend/app/schemas/task_schedule.py`
  - Normalized recurring schedule pattern model

## Frontend Hotspots

- `frontend/src/components/common/HelpTooltip.vue`
  - `?` help icon next to properties, shows description popup on hover
- `frontend/src/views/SnapshotsView.vue`
  - Dedicated snapshot management page with filtering, delete, rollback, and detail drawer
- `frontend/src/views/SchedulesView.vue`
  - Recurring workflow page for scheduled `scrub` and scheduled `snapshot`
  - Supports minutely, hourly, daily, weekly, and monthly snapshot definitions
- `frontend/src/views/TasksView.vue`
  - Task records and status page with pagination and status filters
- `frontend/src/views/DatasetsView.vue`
  - Dataset tree and quick manual snapshot creation entry
- `frontend/src/services/api.js`
  - Auth, settings, disk, pool, dataset, snapshot, task, and schedule APIs
- `frontend/src/views/SettingsView.vue`
  - Active and idle poller interval configuration
  - Idle refresh subsection with per-job idle intervals

## Persistence and Recovery

- `backend/config/tasks.sqlite3`
  - SQLite storage for tasks and task schedules
- `backend/app/services/task_store.py`
  - Persistence layer for tasks and schedules
- `backend/app/services/task_recovery.py`
  - Startup recovery and task reconciliation
- `backend/config/config.json`
  - Polling, SSH, login, and operator-defined disk label settings

## Deployment Entry Points

- `Dockerfile`
  - Builds the frontend with Node, runs the backend on Python, and installs Nginx
- `docker/start.sh`
  - Starts Uvicorn and Nginx together and handles container shutdown signals
- `docker/nginx.conf`
  - Serves the SPA and proxies `/api/` and `/ws/`
- `compose.example.yaml`
  - Example ports, environment overrides, and `/data` persistence volume

## Change Clusters

- Client-aware polling
  - `backend/app/core/client_tracker.py`
  - `backend/app/services/poller.py`
  - `backend/app/api/ws.py`
  - `backend/app/core/config.py`
  - `frontend/src/views/SettingsView.vue`
- SMART health monitoring
  - `backend/app/ssh/commands.py` — `SMART_INFO` command
  - `backend/app/ssh/parser.py` — `parse_smartctl_output`, `parse_smart_info`
  - `backend/app/schemas/zfs_state.py` — `SmartOverview`, `DiskSmartInfo`, `SmartAttributeItem`
  - `backend/app/services/poller.py` — smart job schedule, caching, state assembly
  - `backend/app/api/routes/disks.py` — `GET /api/disks/{key}/smart`, `POST /api/disks/{key}/smart/refresh`
  - `backend/app/core/config.py` — smart interval settings
  - `frontend/src/views/DisksView.vue` — inline health column, SMART detail dialog
  - `frontend/src/views/SettingsView.vue` — active/idle smart intervals
  - `frontend/src/services/api.js` — `getDiskSmartData`, `refreshDiskSmartData`
  - `frontend/src/i18n/messages/*/disks.js` — SMART translation keys
  - `backend/tests/fixtures/smart_info_sample.txt` — ATA + NVMe parser/debug sample (not yet loaded by automated tests or the fixture poller)
- Snapshot management
  - `backend/app/services/snapshot_creator.py`
  - `backend/app/services/snapshot_destroyer.py`
  - `backend/app/services/snapshot_rollbacker.py`
  - `backend/app/services/snapshot_query.py`
  - `frontend/src/views/SnapshotsView.vue`
- Scheduled snapshot and retention
  - `backend/app/services/task_scheduler.py`
  - `backend/app/services/snapshot_metadata.py`
  - `backend/app/services/snapshot_retention.py`
  - `backend/app/schemas/task_schedule.py`
  - `frontend/src/views/SchedulesView.vue`
- Task system
  - `backend/app/services/task_manager.py`
  - `backend/app/services/task_store.py`
  - `backend/app/services/task_recovery.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
