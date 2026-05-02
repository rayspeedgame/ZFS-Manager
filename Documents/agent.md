# Agent Guide

这份文档面向后续接手项目的开发者或智能体，目标是让新成员快速理解“状态从哪里来、写操作怎么落下去、哪些地方最容易出错”。

## 技术栈

- 后端：FastAPI + Pydantic + async SSH
- 前端：Vue 3 + Vite
- 数据传输：REST + WebSocket

## 先建立的三个核心概念

### 1. 快照是唯一界面数据源

前端主要消费：

- `snapshot.meta`
- `snapshot.data.summary`
- `snapshot.data.disks`
- `snapshot.data.pools`
- `snapshot.data.datasets`

不要让前端自己推断 ZFS 真实状态，优先让后端把结构整理好再传。

### 2. pool 写操作是“执行命令 + 强制刷新”

所有 pool 写接口都遵循同一模式：

1. 校验输入
2. 通过 SSH 执行命令
3. 立即 `refresh_once(force_all=True)`
4. 返回结果和刷新错误

### 3. 设备识别不能只看字符串

`zpool status` 里常见的是 `/dev/disk/by-id/...`，而 `lsblk` 里常见的是 `/dev/sdX` 或 `/dev/nvme...`。  
当前代码会把：

- by-id 名称
- 实际分区路径
- 父磁盘路径

统一打通，避免把拓扑成员错误映射到别的盘。

## 维护 pool 功能时先看哪里

- 读链路
  - `backend/app/services/poller.py`
  - `backend/app/ssh/parser.py`
- 写链路
  - `backend/app/api/rest.py`
  - `backend/app/services/pool_creator.py`
  - `backend/app/services/topology_updater.py`
  - `backend/app/services/pool_destroyer.py`
  - `backend/app/services/pool_remover.py`
- 前端
  - `frontend/src/views/PoolsView.js`
  - `frontend/src/store/state.js`

## 当前特别容易踩坑的点

- `zpool destroy` 后磁盘仍可能保留 `zfs_member` 标签
  - 当前会显示为 `zfs_member (inactive)`
  - 同时允许再次用于建池或附加设备
- pool 写操作后不能只等 WebSocket
  - 前端还会主动调用一次 `/api/state`
- 拓扑移除目标不要让前端自己猜
  - 当前后端会生成 `removalTargets`

## 推荐维护方式

- 优先从 fixture 和真实 `zpool status` 输出来校验解析结果
- 前端只消费结构化字段，不再自己猜 pool 成员类别
- 给高风险功能先加后端白名单校验，再加 UI 入口
