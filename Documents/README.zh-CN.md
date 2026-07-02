# Documents

> [English Version](./README.md)

`Documents/` 用于存放项目级设计说明、路线图和代码结构索引。

## 索引

- `agent.md`
  - 协作约定和交接说明
- `target.md`
  - 当前产品目标和已交付能力
- `Roadmap.md`
  - 后续阶段性规划
- `TaskSystemArchitecture.md`
  - 任务持久化、恢复、调度和扩展设计
- `SnapshotManagementArchitecture.md`
  - 快照页、定时快照和保留策略设计
- `PoolMaintenanceArchitecture.md`
  - pool 维护、设备身份、replace 和 RAID-Z expansion 设计
- `ProjectStruction.md`
  - 高层结构概览
- `ProjectDirectoryStructure.md`
  - 逐级目录结构说明

## 当前重点

- 后端采用 SSH 轮询加 REST 写操作的架构。
- 任务系统已经具备 SQLite 持久化、启动恢复、分页查询和状态筛选。
- 快照调度已经支持从分钟到月的多级计划。
- 定时快照使用短名称，计划归属写入 ZFS 用户自定义属性。
- pool 维护已覆盖：
  - `scrub`
  - `clear`
  - `offline / online`
  - `replace`
  - RAID-Z `expansion`
- 磁盘身份模型已经拆分为显示字段和执行字段：
  - `displayName`
  - `commandPath`
  - `commandTarget`
  - `rawCommandTarget`
  - `aliases`
- **客户端感知轮询** — 轮询器根据 WebSocket 客户端存在与否自动在活跃（快速）和空闲（慢速）刷新节奏之间切换。`client_tracker` 模块追踪已连接客户端数量，轮询器将 1 秒固定模式检测与可配置的唤醒/作业刷新间隔解耦。所有空闲间隔均可在设置界面中调整。

## 当前约束

- 未加入 pool 的新设备尽量使用 `by-id`。
- 已在 pool 内的现有成员维护命令必须使用 `zpool status -L` 给出的真实成员名。
- 长时间任务尽量以 ZFS 和主机状态作为真相源。
- RAID-Z expansion 的恢复不仅看 `expand:`，还要看自动 `scrub` 阶段和成员变化。
