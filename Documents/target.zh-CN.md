# Target

> [English Version](./target.md)

## 当前产品目标

将 ZFS Manager 打造成适合单机或小型实验环境的 ZFS Web 管理界面，让常见的 pool、dataset、snapshot、task 和 schedule 工作流不必频繁切换到命令行。

## 已交付能力

### Pool 工作流

- pool 健康、容量和状态概览
- pool 拓扑可视化
- pool 属性编辑
- 增加 `log`、`cache`、`special`、`dedup`、`spare` 设备
- 创建和销毁 pool
- 移除支持的拓扑目标
- 启动和停止 `scrub`
- 在 pool 详情中展示 `scrub` 状态、进度和 ETA
- pool 级 `clear`
- 设备级 `offline / online`
- 设备级 `replace`
- `resilver` 跟踪与恢复
- RAID-Z `expansion`

### Dataset 与快照工作流

- dataset 和 zvol 清单
- 可展开的 dataset 树
- 创建和销毁 dataset / zvol 子项
- 编辑 dataset 属性
- 在 `DatasetsView` 中快速创建快照
- 独立 `SnapshotsView`
- 快照分页、筛选、详情、删除与回滚
- 高级回滚模式：普通、`-r`、`-R`

### 任务与计划任务工作流

- 独立任务记录和状态页
- pool、dataset、snapshot 写操作统一纳入任务系统
- SQLite 任务持久化
- 未完成任务的启动恢复与对账
- 定时 `scrub`
- 定时 `snapshot`
- 基于计划归属的快照保留清理
- 快照计划级别：
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## 当前架构方向

- `SnapshotsView` 是集中快照管理入口
- `DatasetsView` 保留轻量快照发起入口
- 定时快照使用短名称，将归属信息写入 ZFS 用户属性
- 保留策略按计划身份匹配，不会误伤手动快照或其他计划生成的快照
- `SchedulesView` 统一承载定时 `scrub` 和定时 `snapshot`
- pool 维护中的设备显示名与执行名已拆分，避免路径变化影响命令提交

## 下一步

- 继续补强定时快照编辑与策略可见性
- 继续补强 replace / RAID-Z expansion 的候选盘说明和审计信息

> **"分层保留"说明：** 当前通过**多计划独立保留**设计已覆盖分层场景 — 不同频率（daily/weekly/monthly）各自创建独立计划，保留逻辑按 `schedule_id` 自动隔离。无需在单个计划内实现复杂的分层规则。
