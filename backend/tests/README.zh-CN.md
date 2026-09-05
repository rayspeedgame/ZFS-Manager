# tests

> [English Version](./README.md)

这里是后端测试目录。

## 当前覆盖范围

- `test_api.py`：`GET /api/state` 的快照结构和 `/docs` 可用性
- `test_ws.py`：WebSocket 初始推送和状态更新
- `test_config.py`：配置模型与示例 JSON 的有效性
- `test_parser.py`：`lsblk`、`blkid`、`zpool status/list`、dataset 列表、属性和 JSON 夹具解析
- `test_ssh_client.py`：SSH 连接失效后的重连行为

## 当前测试重点

- `AppState(meta, data)` 结构
- `summary / disks / pools / datasets` 新结构
- `AppState` 的汇总、磁盘、pool 和 dataset 数据结构
- 单 pool、多 pool 与空结果等解析边界
- 配置示例可被当前 Pydantic 模型加载

## 尚未覆盖

- pool、dataset、snapshot 写接口及任务生命周期
- 计划任务执行、恢复与保留策略
- ATA/NVMe SMART JSON 解析、轮询和接口

`fixtures/smart_info_sample.txt` 目前是解析和调试样例；fixture 模式不会自动把它注入 SMART 轮询结果。
