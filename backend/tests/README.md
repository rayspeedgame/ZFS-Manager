# tests

这里是后端测试目录。

## 当前覆盖范围

- `test_api.py`: REST 快照接口
- `test_ws.py`: WebSocket 推送
- `test_config.py`: 配置读取
- `test_parser.py`: 命令解析，包含多 pool `zpool status` 场景
- `test_ssh_client.py`: SSH 客户端行为

## 当前测试重点

这一阶段新增或强化的关注点：

- `AppState(meta, data)` 结构
- 保留旧快照后的接口输出
- 多 pool 拓扑解析
- 前端依赖的新领域数据结构
