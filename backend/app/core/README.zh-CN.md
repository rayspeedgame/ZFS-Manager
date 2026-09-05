# core

> [English Version](./README.md)

这一层放置后端基础设施代码。

## 文件说明

- `config.py`: 配置读取、保存、路径解析和环境变量覆盖
- `auth.py`: 登录开关判断、cookie 读写和认证检查
- `client_tracker.py`：跟踪 WebSocket 客户端数量，供活跃/空闲轮询间隔选择使用
- `state.py`: 保存当前应用快照，供 REST 和 WebSocket 共享

## 配置重点

- 默认配置目录是 `backend/config/`
- 仍兼容旧的 `backend/config.json` 作为回退路径
- 也支持 `ZFS_MANAGER_CONFIG` 指定自定义配置文件

主要配置块：

- `poller`（含 `smart_interval_seconds` / `idle_smart_interval_seconds`）
- `ssh`
- `auth`
- `disk_labels`

这些配置允许把高频状态和低频属性分开刷新，也允许通过设置页直接调整连接和登录行为。

任务记录默认保存到配置目录中的 SQLite 数据库，也可通过 `ZFS_MANAGER_TASK_DB` 指定独立路径。
