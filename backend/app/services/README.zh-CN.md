# services

> [English Version](./README.md)

这一层负责后端运行时的核心行为，尤其是轮询、缓存、写操作执行、任务持久化、计划调度和恢复。

## 文件说明

- `poller.py`：调度不同频率的 SSH 刷新任务，维护快照缓存，并生成 `summary / disks / pools / datasets`
- `pool_creator.py`：生成并执行原子化 `zpool create`
- `property_updater.py`：执行 `zpool set`
- `topology_updater.py`：执行 `zpool add`
- `pool_destroyer.py`：执行 `zpool destroy`
- `pool_remover.py`：执行 `zpool remove`
- `pool_scrubber.py`：执行 `zpool scrub` 和 `zpool scrub -s`
- `dataset_creator.py`：执行 `zfs create`
- `dataset_property_updater.py`：执行 `zfs set`
- `dataset_destroyer.py`：执行 `zfs destroy`
- `task_manager.py`：运行态任务生命周期管理
- `task_store.py`：基于 `SQLite` 的任务与计划任务持久化
- `task_recovery.py`：恢复注册表与任务对账服务
- `task_scheduler.py`：周期计划任务调度器

## 当前设计

- `StatePoller` 按不同频率刷新 `pools / datasets / disks / properties`
- 写接口不直接修改内存快照，而是重新采集真实主机状态
- dataset 的层级、父子关系和显示顺序由后端统一整理，再传给前端
- 任务执行与任务展示分离：
  - 执行器负责跑命令
  - 任务服务负责持久化和对账运维可见记录
- 定时 `scrub` 与手动操作共享同一套任务系统
