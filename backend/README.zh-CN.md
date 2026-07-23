# Backend

> [English Version](./README.md)

后端负责 SSH 轮询、REST 写操作、任务持久化、计划执行和恢复。

## 当前职责

- 轮询 `lsblk`、`blkid`、`zpool`、`zfs`、SMART（`smartctl --json`）状态
- 将 pool、dataset、disk、snapshot、属性、SMART 状态整理成统一快照
- 执行 pool、dataset、snapshot 的写操作
- 使用 SQLite 持久化任务与计划任务
- 在重启后恢复未完成任务
- 运行定时 `scrub`
- 运行定时 `snapshot`
- 执行按计划归属隔离的快照保留清理
- 客户端感知的活跃/空闲轮询节奏——有浏览器查看时快速刷新，无浏览器时使用慢速空闲间隔
- 非物理磁盘过滤（`loop`、`ram`、`fd`、`sr`、`zd`、`zram` 排除在磁盘行和总数统计之外）

## 磁盘身份模型

后端会把每块磁盘拆成显示字段和执行字段：

- `displayName`
  - 前端主名称
- `kernelPath`
  - 内核路径，例如 `/dev/sdb`
- `byIdPath`
  - 首选稳定别名
- `commandPath`
  - 未加入 pool 的磁盘执行创建/添加/候选选择时优先使用的路径
- `diskId`
  - 前端展示用稳定标识
- `diskKey`
  - 本地保存自定义名称时使用的稳定键
- `aliases`
  - 刷新前后做宽松匹配的别名集合

对于已经在 pool 内的成员设备：

- 不使用 `commandPath`
- 使用 `zpool status -L` 返回的真实成员名 `commandTarget`

## 当前重点模块

- `app/api/`
  - REST API（路由拆分在 `routes/` 子模块中）和 WebSocket 端点
- `app/core/client_tracker.py`
  - 追踪已连接的 WebSocket 客户端数量，驱动活跃↔空闲轮询模式切换
- `app/services/poller.py`
  - 状态采集、磁盘身份规范化、`scanStatus` / `expandStatus` 组装
  - 客户端感知的活跃/空闲刷新节奏，每项作业间隔独立可配
- `app/services/task_scheduler.py`
  - 定时任务调度
- `app/services/task_store.py`
  - SQLite 持久化
- `app/services/task_recovery.py`
  - 启动恢复、对账、RAID-Z expansion 两阶段恢复
- `app/services/snapshot_metadata.py`
  - 定时快照的 ZFS 用户属性定义
- `app/services/snapshot_retention.py`
  - 短名称快照和保留策略执行
- `app/services/pool_replacer.py`
  - replace 提交
- `app/services/pool_raidz_expander.py`
  - RAID-Z expansion 提交
