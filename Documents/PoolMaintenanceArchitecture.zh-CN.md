# Pool 维护架构

> [English Version](./PoolMaintenanceArchitecture.md)

本文档描述 pool 维护能力在当前项目中的分层方式，以及近期已经落地的维护链路。

## 目标

- 让 pool 级维护动作通过统一的前端入口和任务系统暴露出来。
- 明确“显示身份”和“执行身份”的差异，避免设备路径变化影响维护命令。
- 让长时间维护任务尽量依赖 `zpool status` 进行恢复，而不是依赖一次性的 SSH 会话。

## 当前已交付能力

- `scrub` 启动、停止、进度展示、任务恢复
- pool 级 `clear`
- 设备级 `offline` / `online`
- 设备级 `replace` 与 `resilver` 跟踪
- RAID-Z vdev 级 `raidz expansion`

## 磁盘与成员身份模型

后端现在将“磁盘身份”和“pool 成员身份”拆开处理。

- `displayName`
  - 用于界面主名称
- `kernelPath`
  - 内核设备路径，例如 `/dev/sdb`
- `byIdPath`
  - 优先展示和新设备操作时使用的稳定路径
- `commandPath`
  - 未加入 pool 的磁盘在“创建 pool / 添加设备 / 选择 replace 新盘 / 选择 raidz expansion 新盘”时优先使用的命令路径
- `commandTarget`
  - 已经在 pool 内的成员执行 `offline / online / remove / replace` 时使用的真实成员名，来源于 `zpool status -L`
- `rawCommandTarget`
  - 当前拓扑快照中记录下来的原始成员标识，主要用于审计和恢复
- `aliases`
  - 宽松匹配用的别名集合

分区成员还会继承父盘的整盘 `by-id` 别名。这样当任务元数据里保存的是整盘 `by-id`，而 pool 拓扑里出现的是 `-part1` 形式时，恢复逻辑仍然能把它们识别成同一块盘。

## 前端分层

### `PoolDetailDrawer`

承担池级信息和轻量维护动作：

- `scrub`
- `clear`
- 维护状态摘要

### `PoolTopologyDrawer`

承担设备级与 vdev 级维护动作：

- 设备 `offline / online`
- 设备 `replace`
- RAID-Z vdev `Expand RAID-Z`

这里展示的是“别名优先”的设备名称，但执行命令时仍由后端回落到正确的执行身份。

## 后端分层

### `poller.py`

负责：

- 采集 `lsblk`、`blkid`、`zpool status -L` 等状态
- 规范化磁盘身份
- 构造 `topologySummary`
- 补充 `scanStatus` 与 `expandStatus`

### 独立维护服务

- `pool_scrubber.py`
- `pool_maintainer.py`
- `pool_replacer.py`
- `pool_raidz_expander.py`

这些服务只负责一类维护命令，避免把所有命令细节都塞进 route。

### `task_recovery.py`

负责把长任务恢复为真实状态：

- `scrub`
- `replace` 后的 `resilver`
- `raidz expansion`

## RAID-Z expansion 规则

项目里实现的不是单盘 `online -e` 扩容，而是 RAID-Z vdev 扩展：

- 前端入口位于 RAID-Z vdev 条目，不位于叶子磁盘条目
- 后端执行 `zpool attach <pool> <raidz-vdev> <new-device>`
- 新盘候选优先使用 `by-id`
- 同一个 pool 存在活动扫描任务时，不允许新的 `raidz expansion`

### 进度与恢复

恢复逻辑按两个阶段处理：

1. `expand` 阶段
   - 读取 `zpool status` 中的 `expand:` 行
   - 总进度映射到前 40%
2. 自动 `scrub` 阶段
   - RAID-Z 扩展完成后，ZFS 会自动进入 `scrub`
   - 读取 `scan:` 行中的 `scrub` 进度
   - 总进度映射到后 40%

只有在以下条件同时满足时，任务才会最终完成：

- `expandStatus.completed = true`
- `scanStatus.completed = true`
- 新成员已经能在目标 vdev 成员列表中识别到
- 当前成员数量大于任务创建前记录的成员数量

如果在合理观测窗口内无法确认上述信号，任务会进入需要人工确认的状态，而不是无限等待。

## 当前接口重点

- `POST /api/pools/{pool_name}/offline`
- `POST /api/pools/{pool_name}/online`
- `POST /api/pools/{pool_name}/clear`
- `POST /api/pools/{pool_name}/replace`
- `POST /api/pools/{pool_name}/raidz-expand`

## 当前状态快照中与维护相关的重要字段

- `pool.status.scan`
- `pool.status.expand`
- `pool.scanStatus`
- `pool.expandStatus`
- `pool.topologySummary[*].items[*].members[*].displayLabel`
- `pool.topologySummary[*].items[*].members[*].kernelPath`
- `pool.topologySummary[*].items[*].members[*].byIdPath`
- `pool.topologySummary[*].items[*].members[*].commandTarget`
- `pool.topologySummary[*].items[*].members[*].rawCommandTarget`
- `pool.topologySummary[*].items[*].members[*].aliases`
- `pool.topologySummary[*].items[*].canRaidzExpand`
- `pool.topologySummary[*].items[*].raidzExpandCandidates`

## 后续方向

- 为 `replace` 和 `raidz expansion` 补更明确的候选盘资格说明
- 继续增强 pool 详情中的维护摘要
- 视实际需要再评估更复杂的容量预检和更细的任务审计
