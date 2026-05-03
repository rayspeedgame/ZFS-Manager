# Project Structure

## 整体分层

### `backend`

后端负责和远端主机交互，并把结果整理成前端可直接消费的快照。

- `api`
  - REST / WebSocket 入口
- `core`
  - 配置、状态存储
- `schemas`
  - 请求响应模型与快照模型
- `services`
  - 轮询、聚合、写操作执行
- `ssh`
  - SSH 命令与解析逻辑

### `frontend`

前端负责把快照转换成界面，并把高风险操作组织成确认流。

- `components/common`
  - 通用抽屉、确认框、空态组件
- `store`
  - WebSocket 状态和 REST 写接口
- `views`
  - Dashboard / Disks / Pools / Datasets

### `Documents`

面向维护者的补充说明，帮助快速建立上下文。

## 当前实现拆分

- 读链路
  - `poller.py` 定时采集并聚合状态
  - `parser.py` 解析 `zpool status`、`zfs list/get`、磁盘信息
- pool 写链路
  - `pool_creator.py`: `zpool create`
  - `topology_updater.py`: `zpool add`
  - `pool_destroyer.py`: `zpool destroy`
  - `pool_remover.py`: `zpool remove`
- dataset 写链路
  - `dataset_creator.py`: `zfs create`
  - `dataset_property_updater.py`: `zfs set`
  - `dataset_destroyer.py`: `zfs destroy`
- 展示链路
  - `PoolsView.js` 负责 pool 属性、拓扑、新建和删除交互
  - `DatasetsView.js` 负责 dataset inventory、snapshot 开关和管理抽屉

## 当前边界

- 已支持 pool 和 dataset 的常见管理能力
- snapshot 当前以只读 inventory 为主，不提供专门的 snapshot 创建/回滚流
- 尚未实现更复杂的 `replace`、`detach`、`offline/online` 等维护动作
