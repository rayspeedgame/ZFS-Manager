# ssh

这一层负责与远程主机交互，并解析命令输出。

## 文件说明

- `commands.py`: 定义 grouped read-only commands
- `client.py`: 建立 SSH 连接并执行命令
- `parser.py`: 把命令输出解析为结构化数据

## 当前能力

- 支持轮询需要的只读命令组
- 支持 pool 与 dataset 写操作时的 SSH 命令执行
- `client.py` 返回详细执行结果，包含 `stdout / stderr / exit_status`

## 当前解析重点

- `zpool status` 支持多 pool 拓扑解析
- `zfs list/get` 同时覆盖 filesystem、volume、snapshot
- overview 解析结果既服务调试，也服务最终结构化页面数据
