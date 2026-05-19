# Target

> [English Version](./target.md)

## 当前产品目标

将 ZFS Manager 打造成适合单机或小型实验环境的实用 ZFS Web 管理界面，让运维人员可以在不频繁切回命令行的情况下完成常见的 pool、dataset、snapshot、任务和计划任务操作。

## 已交付能力

### 存储池能力

- 存储池健康、容量和状态总览
- 拓扑可视化
- 可编辑的 pool 属性
- 添加 `log`、`cache`、`special`、`dedup`、`spare` 设备
- 创建与销毁 pool
- 移除支持的拓扑目标
- 启动与停止 `scrub`
- 在 pool 详情中显示 `scrub` 状态、进度和 ETA

### 数据集与快照能力

- dataset 与 zvol 清单
- 可展开的数据集树
- 创建与销毁 dataset / zvol 子项
- 编辑 dataset 属性
- 从 `DatasetsView` 快速创建快照
- 独立的 `SnapshotsView`
- 快照列表分页、筛选、详情、删除与回滚
- 支持安全回滚、`-r`、`-R` 的高级回滚模式

### 任务与计划任务能力

- 独立的任务记录与状态页面
- pool、dataset、snapshot 写操作统一进入任务系统
- 基于 SQLite 的任务持久化
- 未完成任务的启动恢复与对账
- 定时 `scrub`
- 定时 `snapshot`
- 按计划归属执行的快照保留清理
- 定时快照级别：
  - 分钟级
  - 小时级
  - 天级
  - 周级
  - 月级

## 当前架构方向

- `SnapshotsView` 作为快照集中管理界面
- `DatasetsView` 保持为轻量的快照发起入口
- 定时快照现在采用短快照名，并通过 ZFS 用户属性记录策略归属
- 保留策略按计划身份匹配，因此不会误删手动快照，也不会影响其他计划生成的快照
- 计划任务页面现在同时承载定时 `scrub` 和定时 `snapshot`

## 下一步

- 将当前定时快照与保留策略行为继续同步进运维文档
- 增强定时快照编辑与策略可视化
- 在需要时从 keep-latest 扩展到更完整的日/周/月分层保留
- 继续推进 replace、resilver 跟踪、expansion 等 pool 维护能力
