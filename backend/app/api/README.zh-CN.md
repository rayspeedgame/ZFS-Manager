# api

> [English Version](./README.md)

这里是后端 HTTP API 层。`rest.py` 现在只作为稳定聚合入口，具体实现已经按资源域拆分到 `routes/`。

## 目录结构

- `rest.py`
  - 路由聚合入口
- `ws.py`
  - WebSocket 状态推送
- `common.py`
  - 通用任务消息和命令日志辅助
- `constants.py`
  - API 边界上的常量和属性白名单
- `validators.py`
  - REST 入参校验和当前快照解析
- `routes/system.py`
  - 系统状态、认证、设置
- `routes/tasks.py`
  - 任务与计划任务
- `routes/disks.py`
  - 磁盘标签、SMART 数据读取
- `routes/pools.py`
  - pool、维护动作、replace、RAID-Z expansion
- `routes/datasets.py`
  - dataset
- `routes/snapshots.py`
  - snapshot

## 当前接口约定

- 状态与设置：`GET /api/state`、`POST /api/state/refresh`、`GET /api/health`、`GET/PUT /api/settings`、`POST /api/settings/test-ssh`
- 认证：`GET /api/auth/status`、`POST /api/auth/login`、`POST /api/auth/logout`
- 磁盘：`PUT /api/disks/{disk_key}/label`、`GET /api/disks/{disk_key}/smart`、`POST /api/disks/{disk_key}/smart/refresh`
- pool：创建、销毁、移除设备、属性更新、scrub 启停、设备 offline/online/replace、RAID-Z expansion、clear 和 topology 更新
- dataset：创建、销毁和属性更新；dataset 名通过 `{dataset_name:path}` 支持 `/`
- snapshot：分页列表、筛选值、详情、按 dataset 查询、创建、删除和回滚；snapshot 名通过 `{snapshot_name:path}` 支持 `/`
- 任务：任务列表/详情，以及计划列表、创建、局部更新和删除
- 实时状态：`WS /ws/state`

快照列表支持 `search`、`pool`、`dataset`、`snapshot_type`、`sort_by`、`sort_order`、`page` 和 `page_size`。

## 当前规则

- 新设备相关选择尽量落到 `commandPath`
- 已在 pool 内的成员维护必须落到 `commandTarget`
- 校验层会接受 `displayName`、`kernelPath`、`byIdPath`、`aliases` 等多种别名
- 但真正执行命令前仍会回落到当前快照里的正确执行目标
- 对现有 pool 的 topology 更新当前只允许添加 `log`、`cache`、`spare`、`special` 和 `dedup`；不允许添加新的 data vdev
- 所有会修改 ZFS 的写操作和计划执行都要求 `poller.mode=ssh`；设置、登录和磁盘标签不受此限制
- 从单盘 SMART 接口发起的手动刷新目前调用 `refresh_once(force_all=True)`，会刷新完整状态，而不只是该磁盘

## 维护相关说明

- `scrub`、`replace/resilver`、RAID-Z `expansion` 都属于任务系统持续跟踪的长时间动作
- RAID-Z `expansion` 不是单盘 `online -e`，而是 vdev 级 `zpool attach`
- 写操作后仍会强制刷新一次当前状态，以便任务恢复层尽快接管后续进度
