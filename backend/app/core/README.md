# core

这一层放置后端基础设施代码。

## 文件说明

- `config.py`: 读取并校验配置，包含 SSH 与轮询参数
- `state.py`: 保存当前应用快照，供 REST 与 WebSocket 共用

## 当前配置重点

轮询相关参数已经从“单一刷新间隔”扩展为更细的计划：

- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`

这让高频状态和低频属性可以分别刷新。
