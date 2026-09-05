# schemas

> [English Version](./README.md)

这一层定义后端对内和对外使用的数据模型。

## 当前重点模型

- `AppState`：顶层快照
- `AppMeta`：应用状态、来源状态、时间和错误信息
- `AppData`：结构化业务数据与兼容 overview，快照中携带 `smart_overview: SmartOverview`
- `SmartOverview`：按设备路径索引的全局 SMART 数据容器
- `DiskSmartInfo`：规范化后的 SMART 信息（健康状态、温度、通电时间、协议类型、属性表）
- `SmartAttributeItem`：单条 SMART 属性（id、名称、值、最差、阈值、原始值、告警状态）
- `PropertyValue`：属性值与来源
- `AppConfig`：设置页读写的完整配置模型
- `SettingsSaveResponse`：设置保存响应
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

## 设计要点

- 保留 overview，便于调试和兼容迁移
- 同时提供 `summary / disks / pools / datasets`，减少前端重复拼装
- 写操作响应尽量保留命令、退出码和标准输出，方便排查
- 任务列表响应现在额外携带分页与筛选元数据，供任务记录页使用
- 快照列表项携带允许删除/回滚等能力标记，前端无需重复推导操作可用性
- 计划模型把频率参数规范化到 `TaskSchedulePattern`，供调度器和 API 复用
