# Agent Guide

这份文档面向后续接手项目的开发者或智能体，目标是让新成员快速理解“状态从哪里来、写操作怎么落下去、哪些地方最容易出错”。

## 技术栈

- 后端：FastAPI + Pydantic + async SSH
- 前端：Vue 3 + Vite
- 传输：REST + WebSocket

## 三个核心概念

### 1. 快照是唯一页面数据源

前端主要消费：

- `snapshot.meta`
- `snapshot.data.summary`
- `snapshot.data.disks`
- `snapshot.data.pools`
- `snapshot.data.datasets`

不要让前端自己推导 ZFS 真实状态，优先让后端把结构整理好再传。

### 2. 写操作遵循“执行命令 + 强制刷新”

pool 和 dataset 写接口都遵循同一模式：

1. 校验输入
2. 通过 SSH 执行命令
3. 立即 `refresh_once(force_all=True)`
4. 返回结果与刷新错误

### 3. dataset 结构现在优先在后端整理

`snapshot.data.datasets` 已经带有：

- `poolName`
- `parentName`
- `depth`
- `shortName`

前端只负责展示、折叠和 snapshot 显示开关，不再自己重建树顺序。

## 维护重点入口

- 读链路
  - `backend/app/services/poller.py`
  - `backend/app/ssh/parser.py`
- 写链路
  - `backend/app/api/rest.py`
  - `backend/app/services/pool_creator.py`
  - `backend/app/services/topology_updater.py`
  - `backend/app/services/dataset_creator.py`
  - `backend/app/services/dataset_property_updater.py`
  - `backend/app/services/dataset_destroyer.py`
- 前端
  - `frontend/src/views/PoolsView.js`
  - `frontend/src/views/DatasetsView.js`
  - `frontend/src/store/state.js`

## 常见易错点

- `zpool destroy` 后磁盘仍可能保留 `zfs_member` 标签
- 顶栏普通状态读取不等于后端已经重新采集，真正全量刷新要走 `/api/state/refresh`
- dataset 名称可能包含 `/`，REST 路由必须使用 `{dataset_name:path}`
- snapshot 数量多时主列表可能噪声较大，所以前端默认关闭 `Show snapshots`
