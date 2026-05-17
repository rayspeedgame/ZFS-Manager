# schemas

> [中文版本](./README.zh-CN.md)

This layer defines the data models used internally and externally by the backend.

## Key Models

- `AppState`: Top-level snapshot
- `AppMeta`: Application status, source status, timestamps, and error information
- `AppData`: Structured business data with legacy overview compatibility
- `PropertyValue`: Property value with source
- `AppConfig`: Complete settings model used by the settings page
- `SettingsSaveResponse`: Settings save response
- `SSHConnectionTestRequest` / `SSHConnectionTestResponse`
- `AuthStatusResponse` / `LoginRequest` / `LoginResponse`
- `PoolCreateRequest` / `PoolCreateResponse`
- `PoolPropertyUpdateRequest` / `PoolPropertyUpdateResponse`
- `PoolTopologyUpdateRequest` / `PoolTopologyUpdateResponse`
- `PoolScrubResponse`
- `DatasetCreateRequest` / `DatasetCreateResponse`
- `DatasetPropertyUpdateRequest` / `DatasetPropertyUpdateResponse`
- `DatasetDestroyResponse`
- `TaskListResponse` / `TaskDetailResponse`
- `TaskScheduleCreateRequest` / `TaskScheduleUpdateRequest`
- `TaskScheduleListResponse` / `TaskScheduleDetailResponse`

## Design Notes

- Preserves overview for debugging and migration compatibility
- Provides `summary / disks / pools / datasets` simultaneously to reduce frontend duplicate assembly
- Write responses try to preserve command, exit code, and stdout for troubleshooting
- Task list responses now carry pagination and filtering metadata for the task records page
