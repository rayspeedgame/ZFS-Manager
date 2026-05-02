# ssh

这一层负责与远端主机交互，并解析命令输出。

## 文件说明

- `commands.py`: 定义分组命令
- `client.py`: 建立 SSH 连接并执行命令
- `parser.py`: 把命令输出解析为结构化数据

## 当前能力

- 支持轮询所需的只读命令组
- 支持 pool 属性写回时的 SSH 命令执行
- `client.py` 提供详细执行结果，包含 `stdout`、`stderr` 和退出码

## 当前解析重点

- `zpool status` 支持多 pool 拓扑解析
- `status_by_pool` 用于 pool 详情和磁盘归属推断
- 解析结果既服务于 overview，也服务于更高层的结构化页面数据
