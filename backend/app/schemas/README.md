# schemas

这一层定义后端对内和对外使用的数据模型。

## 当前重点模型

- `AppState`: 顶层快照
- `AppMeta`: 应用状态、来源状态、时间和错误信息
- `AppData`: 结构化业务数据与兼容 overview
- `PropertyValue`: 属性值与来源
- `AppConfig`: 设置页读写的完整配置模型
- `SettingsSaveResponse`: 设置保存响应
- `SSHConnectionTestRequest` / `SSHConnectionTestResponse`
- `AuthStatusResponse` / `LoginRequest` / `LoginResponse`
- `PoolCreateRequest` / `PoolCreateResponse`
- `PoolPropertyUpdateRequest` / `PoolPropertyUpdateResponse`
- `PoolTopologyUpdateRequest` / `PoolTopologyUpdateResponse`
- `DatasetCreateRequest` / `DatasetCreateResponse`
- `DatasetPropertyUpdateRequest` / `DatasetPropertyUpdateResponse`
- `DatasetDestroyResponse`

## 设计要点

- 保留 overview，便于调试和兼容迁移
- 同时提供 `summary / disks / pools / datasets`，减少前端重复拼装
- 写操作响应尽量保留命令、退出码和标准输出，方便排查
