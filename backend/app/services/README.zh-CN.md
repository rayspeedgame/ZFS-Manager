# services

> [English Version](./README.md)

这里集中放置后端服务层：状态采集、任务系统、计划调度、快照策略和 pool 维护执行器。

## 主要文件

- `poller.py`
  - 采集 SSH 状态、规范化磁盘身份、组装应用快照
- `task_manager.py`
  - 任务注册、状态更新、查询
- `task_store.py`
  - SQLite 持久化
- `task_recovery.py`
  - 启动恢复与任务对账
- `task_scheduler.py`
  - 定时 `scrub` 和定时 `snapshot`
- `snapshot_metadata.py`
  - ZFS 用户属性定义
- `snapshot_retention.py`
  - 短名称定时快照与保留清理
- `pool_scrubber.py`
  - `scrub` 命令提交
- `pool_maintainer.py`
  - `clear`、`offline`、`online`
- `pool_replacer.py`
  - `replace`
- `pool_raidz_expander.py`
  - RAID-Z `expansion`

## 当前约定

### 磁盘与成员身份

`poller.py` 会同时构造磁盘级和 pool 成员级身份：

- 磁盘行会暴露 `displayName`、`kernelPath`、`byIdPath`、`commandPath`、`diskId`、`diskKey`、`aliases`
- pool 叶子成员会暴露 `displayLabel`、`kernelPath`、`byIdPath`、`commandTarget`、`rawCommandTarget`、`aliases`

分区成员还会继承父盘的整盘 `by-id` 别名，避免恢复逻辑因为整盘路径和 `-part1` 路径不同而漏判同一块盘。

### pool 维护命令

- 新设备相关操作优先使用 `commandPath`
- 已在 pool 内的成员维护必须使用 `commandTarget`

### RAID-Z expansion 恢复

`task_recovery.py` 现在会同时观察：

- `expand:` 行
- 自动 `scrub` 的 `scan:` 行
- 目标 vdev 是否出现新成员
- 成员数是否增长

只有这些条件闭合后，RAID-Z expansion 任务才会进入完成状态。
