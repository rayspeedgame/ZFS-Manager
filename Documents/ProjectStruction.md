# Project Structure

## 整体分层

### `backend`

后端负责和远端主机交互，并把结果整理成前端可直接消费的快照。

- `api`
  - REST / WebSocket 入口
- `core`
  - 配置、状态存储
- `schemas`
  - 请求响应模型
- `services`
  - 轮询、聚合、写操作执行
- `ssh`
  - SSH 命令和解析逻辑

### `frontend`

前端负责把快照转成界面，并把高风险操作组织成确认流。

- `components/common`
  - 通用抽屉、确认框、空态组件
- `store`
  - WebSocket 状态和 REST 写接口
- `views`
  - Dashboard / Disks / Pools / Datasets

### `Documents`

面向维护者的补充说明，帮助快速建立上下文。

## pool 相关实现拆分

- “读”链路
  - `poller.py` 定时采集并聚合状态
  - `parser.py` 解析 `zpool status`、`blkid`、`/dev/disk/by-id`
- “写”链路
  - `pool_creator.py`: `zpool create`
  - `topology_updater.py`: `zpool add`
  - `pool_destroyer.py`: `zpool destroy`
  - `pool_remover.py`: `zpool remove`
- “展示”链路
  - `PoolsView.js` 负责属性、拓扑、新建、删除、移除交互
  - `DisksView.js` 负责磁盘和 inactive 标签展示

## 当前边界

- 支持添加附加设备：`log`、`cache`、`special`、`dedup`、`spare`
- 新建 pool 支持 `data vdev` 和附加设备一起原子化提交
- 删除 pool 已支持
- 拓扑移除当前走 `zpool remove`
- 还没有实现更复杂的 `replace`、`detach`、`offline` 等维护动作
