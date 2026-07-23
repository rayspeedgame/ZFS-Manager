# ssh

> [English Version](./README.md)

这一层负责与远程主机交互，并解析命令输出。

## 文件说明

- `commands.py`: 定义 grouped read-only commands
- `client.py`: 建立 SSH 连接并执行命令
- `parser.py`: 把命令输出解析为结构化数据

## 当前能力

- 支持轮询需要的只读命令组
- 支持 pool 与 dataset 写操作时的 SSH 命令执行
- `client.py` 返回详细执行结果，包含 `stdout / stderr / exit_status`
- `SMART_INFO` 命令对所有非虚拟块设备采集 `smartctl -a --json`，已过滤 `loop`、`ram`、`fd`、`sr`、`zd`、`zram`

## 当前解析重点

- `zpool status` 支持多 pool 拓扑解析
- `zfs list/get` 同时覆盖 filesystem、volume、snapshot
- `smartctl --json` 输出被解析为结构化 `SmartOverview`，按设备存储 `DiskSmartInfo`：
  - 支持 ATA 属性表（`ata_smart_attributes.table`）和 NVMe 健康日志（`nvme_smart_health_information_log`）
  - 协议类型规范化：`sat` → `sata`，其余原样保留
- overview 解析结果既服务调试，也服务最终结构化页面数据
