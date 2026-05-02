# ssh

这一层负责所有与远端主机交互或解析命令输出的逻辑。

## 文件说明

- `commands.py`: 定义分组命令
- `client.py`: 建立 SSH 连接并执行命令
- `parser.py`: 把命令输出解析为结构化数据

## 当前命令分组

为了配合分频轮询，命令已经按用途拆开：

- `DISK_OVERVIEW`
- `ZPOOL_CORE`
- `ZPOOL_PROPERTIES`
- `ZFS_DATASET_CORE`
- `ZFS_DATASET_PROPERTIES`

## 当前解析重点

- `zpool status` 已支持多 pool 拓扑解析
- `status_by_pool` 用于池详情和磁盘归属推断
- 解析结果既服务于 overview，也服务于更高层的领域数据构建
