# tests

这里是后端测试目录。

## 当前覆盖范围

- `test_api.py`: REST 快照与写接口
- `test_ws.py`: WebSocket 推送
- `test_config.py`: 配置读取
- `test_parser.py`: 命令解析，包含 dataset / snapshot / 多 pool 场景
- `test_ssh_client.py`: SSH 客户端行为

## 当前测试重点

- `AppState(meta, data)` 结构
- `summary / disks / pools / datasets` 新结构
- pool / dataset 写操作返回结果格式
- `zfs list/get` 对 snapshot 的解析
