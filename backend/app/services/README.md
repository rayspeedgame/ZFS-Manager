# services

这一层负责后端运行时的核心行为，尤其是轮询、缓存、快照组装和写操作执行。

## 文件说明

- `poller.py`: 调度不同频率的 SSH 刷新任务，维护快照缓存，并生成 `summary / disks / pools / datasets`
- `pool_creator.py`: 生成并执行原子化 `zpool create`
- `property_updater.py`: 执行 `zpool set`
- `topology_updater.py`: 执行 `zpool add`
- `pool_destroyer.py`: 执行 `zpool destroy`
- `pool_remover.py`: 执行 `zpool remove`
- `dataset_creator.py`: 执行 `zfs create`
- `dataset_property_updater.py`: 执行 `zfs set`
- `dataset_destroyer.py`: 执行 `zfs destroy`

## 当前设计

- `StatePoller` 按 `pools / datasets / disks / properties` 分频刷新
- 写接口不直接修改内存快照，而是重新采集真实主机状态
- dataset 的层级、父子关系和显示顺序由后端统一整理，再传给前端
