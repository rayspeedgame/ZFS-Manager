# Roadmap

> [English Version](./Roadmap.md)

## 已完成或正在使用的基础能力

- 任务记录和状态页
- 任务与计划任务的 SQLite 持久化
- 启动恢复与任务对账
- 手动 `scrub`
- 定时 `scrub`
- 独立快照页
- 快照创建、删除、回滚和高级回滚
- 定时快照
- 基于计划归属的快照保留清理
- pool 级 `clear`
- 设备级 `offline / online`
- `replace` 与 `resilver` 跟踪
- RAID-Z `expansion`
- 客户端感知的活跃/空闲轮询节奏，连接时即时全量刷新
- 设置界面中可配置的空闲间隔

## 当前快照方向

- `DatasetsView` 仍然负责快速手动创建快照
- `SnapshotsView` 是集中管理入口
- 定时快照使用短名称，例如 `scheduled-YYYYMMDD-HHMMSS-random`
- 策略归属、频率、递归和保留信息写入 ZFS 用户属性
- 清理逻辑按计划身份分组，不会影响手动快照或其它计划的快照
- 计划级别支持：
  - minutely
  - hourly
  - daily
  - weekly
  - monthly

## 当前 pool 维护方向

- 新设备加入和计划中的新盘选择优先使用 `by-id`
- 已在 pool 内的现有成员维护必须使用 `commandTarget`
- RAID-Z expansion 使用 vdev 级入口，不使用叶子盘入口
- RAID-Z expansion 的恢复采用：
  - `expand:` 阶段
  - 自动 `scrub` 阶段
  - 新成员识别与成员数量变化

## 下一阶段重点

### 1. 快照计划细化

- 编辑已有快照计划
- 在界面中更清楚展示策略归属和元数据
- 增加“哪些快照属于哪个计划”的可见性

### 2. 快照保留策略增强

- 当前 `keep latest N` 作为基线
- 继续保证自动清理不影响手动快照

> **"分层保留"已被多计划设计覆盖：** 系统通过**多计划独立保留**天然实现了分层效果。
> 用户只需为不同频率（如 daily、weekly、monthly）分别创建独立计划，每个计划各自保留最新 N 个快照，
> 保留逻辑按 `schedule_id` 在 ZFS 用户属性中匹配，不会误删其他计划或手动快照。
> 因此无需在单个计划内实现复杂的分层保留规则。

### 3. pool 维护增强

- 更清晰的 replace 候选盘资格说明
- 更清晰的 RAID-Z expansion 候选盘资格说明
- 更完整的 pool 维护摘要与审计信息

### 4. 文档与审计完善

- 保持计划任务、保留策略、任务恢复和 pool 维护文档一致
- 继续增强任务日志和操作审计信息
