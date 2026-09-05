# schemas

> [中文版本](./README.zh-CN.md)

This layer defines the data models used internally and externally by the backend.

## Key Models

- `AppState`: Top-level snapshot
- `AppMeta`: Application status, source status, timestamps, and error information
- `AppData`: Structured business data with legacy overview compatibility, carries `smart_overview: SmartOverview` in the snapshot
- `SmartOverview`: Per-device SMART data container indexed by device path
- `DiskSmartInfo`: Normalized SMART info (health status, temperature, power-on hours, protocol, attributes)
- `SmartAttributeItem`: Individual SMART attribute (id, name, value, worst, threshold, raw, when_failed)
- `PropertyValue`: Property value with source
- `AppConfig`: Complete settings model used by the settings page
- `SettingsSaveResponse`: Settings save response
- `SSHConnectionTestRequest` / `SSHConnectionTestResponse`
- `AuthStatusResponse` / `LoginRequest` / `LoginResponse`
- `DiskLabelUpdateRequest` / `DiskLabelUpdateResponse`
- `PoolCreateRequest` / `PoolCreateResponse`
- `PoolDestroyResponse` / `PoolRemoveRequest` / `PoolRemoveResponse`
- `PoolPropertyUpdateRequest` / `PoolPropertyUpdateResponse`
- `PoolTopologyUpdateRequest` / `PoolTopologyUpdateResponse`
- `PoolScrubResponse` / `PoolDeviceActionRequest` / `PoolMaintenanceActionResponse`
- `PoolReplaceRequest` / `PoolReplaceResponse`
- `PoolRaidzExpandRequest` / `PoolRaidzExpandResponse`
- `DatasetCreateRequest` / `DatasetCreateResponse`
- `DatasetPropertyUpdateRequest` / `DatasetPropertyUpdateResponse`
- `DatasetDestroyResponse`
- `SnapshotListResponse` / `SnapshotDetailResponse` / `SnapshotFiltersResponse`
- `SnapshotCreateRequest` / `SnapshotCreateResponse`
- `SnapshotDestroyResponse` / `SnapshotRollbackRequest` / `SnapshotRollbackResponse`
- `TaskListResponse` / `TaskDetailResponse`
- `TaskScheduleCreateRequest` / `TaskScheduleUpdateRequest`
- `TaskScheduleListResponse` / `TaskScheduleDetailResponse`

## Design Notes

- Preserves overview for debugging and migration compatibility
- Provides `summary / disks / pools / datasets` simultaneously to reduce frontend duplicate assembly
- Write responses try to preserve command, exit code, and stdout for troubleshooting
- Task list responses now carry pagination and filtering metadata for the task records page
- Snapshot list items carry capability flags such as whether delete or rollback is allowed, so the frontend does not have to re-derive action availability
- Schedule models normalize frequency parameters into `TaskSchedulePattern` for reuse by the scheduler and API
