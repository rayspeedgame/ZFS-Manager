# services

> [English Version](./README.md)

这一层负责后端运行时行为，重点包括轮询、写操作执行、任务持久化、周期调度和恢复。

## 重点文件

- `poller.py`：采集 SSH 状态并组装共享应用快照
- `task_manager.py`：运行时任务生命周期管理
- `task_store.py`：基于 SQLite 的任务与计划任务持久化
- `task_recovery.py`：启动恢复与对账
- `task_scheduler.py`：负责 `scrub` 与 `snapshot` 的周期任务调度
- `snapshot_metadata.py`：定时快照的 ZFS 用户属性键定义
- `snapshot_retention.py`：定时快照命名与 keep-latest 保留规划
- `snapshot_query.py`：从快照属性中读回计划归属字段

## 当前设计说明

- 定时快照现在依赖 ZFS 用户属性记录归属和保留身份
- 保留清理按计划范围执行，并按数据集分别计算
- 所有写接口都通过刷新实时状态完成结果对齐，而不是直接假设前端状态
