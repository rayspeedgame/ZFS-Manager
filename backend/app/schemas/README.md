# schemas

这一层定义后端对内和对外使用的数据模型。

## 当前重点模型

- `AppState`: 顶层快照
- `AppMeta`: 运行状态、来源状态、错误与时间信息
- `AppData`: 结构化业务数据与兼容 overview
- `PropertyValue`: 属性值与来源
- `PoolPropertyUpdateRequest`: pool 属性写回请求
- `PoolPropertyUpdateResult`: 单个属性的写回结果
- `PoolPropertyUpdateResponse`: 一次提交的整体结果

## 设计要点

- 保留 overview，方便调试和兼容迁移
- 新增 `summary/disks/pools/datasets`，减少前端重复拼装
- 写回结果中保留 `command`、`exit_status`、`stdout`、`stderr`，便于排查 SSH 失败原因
