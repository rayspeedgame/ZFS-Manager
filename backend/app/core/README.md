# core

这一层放置后端基础设施代码。

## 文件说明

- `config.py`: 读取并校验配置，包含轮询与 SSH 参数
- `state.py`: 保存当前应用快照，供 REST 与 WebSocket 共享

## 配置重点

- `poller.mode`: `fixture` 或 `ssh`
- `poller.fallback_to_fixture`: SSH 失败时是否回退到 fixture
- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`

这些配置允许高频状态和低频属性分开刷新。
