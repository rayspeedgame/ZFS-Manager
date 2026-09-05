# ssh

> [English Version](./README.md)

这一层负责与远程主机交互，并解析命令输出。

## 文件说明

- `commands.py`: 定义 grouped read-only commands
- `client.py`: 建立 SSH 连接并执行命令
- `parser.py`: 把命令输出解析为结构化数据

## 当前能力

- 支持轮询需要的只读命令组
- 支持 pool、dataset、snapshot 和计划任务写操作时的 SSH 命令执行
- `client.py` 返回详细执行结果，包含 `stdout / stderr / exit_status`
- `SMART_INFO` 命令对所有非虚拟块设备采集 `smartctl -a --json`，已过滤 `loop`、`ram`、`fd`、`sr`、`zd`、`zram`

## 当前解析重点

- `zpool status` 支持多 pool 拓扑解析
- `zfs list/get` 同时覆盖 filesystem、volume、snapshot
- `smartctl --json` 输出被解析为结构化 `SmartOverview`，按设备存储 `DiskSmartInfo`：
  - 支持 ATA 属性表（`ata_smart_attributes.table`）和 NVMe 健康日志（`nvme_smart_health_information_log`）
  - 协议类型规范化：`sat` → `sata`，其余原样保留
- overview 解析结果既服务调试，也服务最终结构化页面数据

## 远端要求

- 目标主机需要提供 `zpool`、`zfs`、`lsblk`、`findmnt`、`blkid` 和 `smartctl`
- SMART 采集依赖远端安装 `smartmontools`，SSH 用户需要有读取磁盘健康信息及执行所启用写操作的权限
- fixture 模式只加载既有状态夹具；不会自动加载 `tests/fixtures/smart_info_sample.txt` 作为 SMART 轮询结果
