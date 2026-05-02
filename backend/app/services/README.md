# services

这一层负责后端运行时的核心行为，尤其是轮询、缓存、快照组装和属性写回。

## 文件说明

- `poller.py`: 调度不同频率的 SSH 刷新任务，维护最近一次成功快照，并生成 `summary`、`disks`、`pools`、`datasets`
- `property_updater.py`: 负责执行 `zpool set` 写回，并为每个属性生成独立的执行结果
- `topology_updater.py`: 负责执行 `zpool add` 拓扑变更，并为每个新增操作生成独立的执行结果

## 当前设计

- `StatePoller` 按 `pools`、`datasets`、`disks`、`properties` 四类任务分频刷新
- 写回接口不会直接修改内存快照，而是调用 `poller.refresh_once()` 重新采集状态
- 写回结果按属性逐项返回，支持部分成功、部分失败的场景
