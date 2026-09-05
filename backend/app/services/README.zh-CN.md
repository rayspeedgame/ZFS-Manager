# services

> [English Version](./README.md)

这里集中放置后端服务层：状态采集、任务系统、计划调度、快照策略和 pool 维护执行器。

## 主要文件

- `poller.py`
  - 采集 SSH 状态、规范化磁盘身份、组装应用快照
  - 五个独立作业调度（disks、pools、datasets、properties、smart），各有活跃/空闲间隔
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
- `pool_creator.py` / `pool_destroyer.py` / `pool_remover.py`
  - pool 创建、销毁和设备移除
- `property_updater.py` / `topology_updater.py`
  - pool 属性和辅助 vdev 拓扑更新
- `dataset_creator.py` / `dataset_destroyer.py` / `dataset_property_updater.py`
  - dataset 与 zvol 的生命周期和属性更新
- `snapshot_creator.py` / `snapshot_destroyer.py` / `snapshot_rollbacker.py` / `snapshot_query.py`
  - 快照查询、创建、删除和回滚

## 当前约定

### 磁盘与成员身份

`poller.py` 会同时构造磁盘级和 pool 成员级身份：

- 磁盘行会暴露 `displayName`、`kernelPath`、`byIdPath`、`commandPath`、`diskId`、`diskKey`、`aliases`
- pool 叶子成员会暴露 `displayLabel`、`kernelPath`、`byIdPath`、`commandTarget`、`rawCommandTarget`、`aliases`
- 非物理块设备（`loop`、`ram`、`fd`、`sr`、`zd`、`zram`）在构造磁盘行前会被过滤

### SMART 健康监控

`poller.py` 包含第五个作业调度（smart），负责采集 `smartctl -a --json` 输出：

- 通过 `smart_interval_seconds` / `idle_smart_interval_seconds` 配置间隔
- ATA 和 NVMe 属性被解析为 `SmartOverview` / `DiskSmartInfo` / `SmartAttributeItem`
- SSH 解析器会把 `sat` 协议规范化为 `sata`，以保证显示一致性
- 通过 `GET /api/disks/{disk_key}/smart` 获取，通过 `POST /api/disks/{disk_key}/smart/refresh` 刷新
- 非物理块设备（`loop`、`ram`、`fd`、`sr`、`zd`、`zram`）在构造磁盘行前会被过滤
- 单盘详情页的手动 SMART 刷新当前会触发一次完整的 `force_all` 状态刷新

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

任务恢复检查会在 runtime 启动、相关 pool 维护/定时 scrub 的写后刷新以及任务接口访问时运行；当前没有独立的后台对账循环。
