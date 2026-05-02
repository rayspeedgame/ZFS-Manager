# schemas

这一层定义后端向内和向外使用的数据模型。

## 当前重点模型

- `AppState`: 顶层快照
- `AppMeta`: 运行状态、来源状态、错误与时间信息
- `AppData`: 结构化业务数据与兼容 overview
- `SummaryRow`、`DiskRow`、`PoolRow`、`DatasetRow`: 前端直接消费的数据行

## 设计要点

- 继续保留原始 overview，方便调试和兼容迁移
- 新增 `summary/disks/pools/datasets`，减少前端重复拼装
- 用 `meta` 明确描述 `ready`、`degraded`、`error`、`disconnected`
