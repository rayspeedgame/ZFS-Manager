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

- `GET /api/state`
  - 返回统一状态快照
- `POST /api/state/refresh`
  - 强制刷新状态
- `GET /api/tasks`
  - 支持分页和状态筛选
- `PUT /api/disks/{disk_key}/label`
  - 保存自定义磁盘名称
- `GET /api/disks/{disk_key}/smart`
  - 返回指定磁盘的缓存 SMART 数据
- `POST /api/disks/{disk_key}/smart/refresh`
  - 强制全量刷新 SMART 数据并返回最新结果
- `POST /api/pools/{pool_name}/offline`
- `POST /api/pools/{pool_name}/online`
- `POST /api/pools/{pool_name}/clear`
- `POST /api/pools/{pool_name}/replace`
- `POST /api/pools/{pool_name}/raidz-expand`

## 当前规则

- 新设备相关选择尽量落到 `commandPath`
- 已在 pool 内的成员维护必须落到 `commandTarget`
- 校验层会接受 `displayName`、`kernelPath`、`byIdPath`、`aliases` 等多种别名
- 但真正执行命令前仍会回落到当前快照里的正确执行目标

## 维护相关说明

- `scrub`、`replace/resilver`、RAID-Z `expansion` 都属于任务系统持续跟踪的长时间动作
- RAID-Z `expansion` 不是单盘 `online -e`，而是 vdev 级 `zpool attach`
- 写操作后仍会强制刷新一次当前状态，以便任务恢复层尽快接管后续进度
