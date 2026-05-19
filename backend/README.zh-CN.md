# Backend

> [English Version](./README.md)

后端负责 SSH 轮询、REST 写操作执行、任务持久化、计划任务执行和恢复逻辑。

## 当前职责

- 通过 `lsblk`、`blkid`、`zpool`、`zfs` 采集主机状态
- 将 pool、dataset、disk、property 状态整理成统一应用快照
- 执行 pool、dataset、snapshot 写操作
- 使用 SQLite 持久化任务和计划任务
- 在重启后恢复未完成任务
- 执行定时 `scrub`
- 执行定时 `snapshot`
- 执行按计划归属范围的快照保留清理

## 当前重点模块

- `app/api/`：REST 接口层
- `app/services/poller.py`：状态采集与快照组装
- `app/services/task_scheduler.py`：周期任务调度器
- `app/services/snapshot_metadata.py`：定时快照的 ZFS 用户属性定义
- `app/services/snapshot_retention.py`：短格式定时快照命名与保留规划
- `app/services/task_store.py`：SQLite 持久化层
- `app/services/task_recovery.py`：启动恢复与对账

## 当前定时快照规则

- 定时快照名称保持简短
- 计划身份写入 ZFS 用户属性
- 清理逻辑通过计划归属属性匹配快照，而不是解析长名称
