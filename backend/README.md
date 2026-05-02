# Backend

后端使用 FastAPI 提供 REST 和 WebSocket 接口，并通过 SSH 轮询远端 ZFS 主机状态。

## 这一阶段的重点

- 状态模型升级为 `meta + data`
- 失败时保留最近一次成功快照
- 轮询拆分为 `pools`、`datasets`、`disks`、`properties`
- 输出前端直接可用的领域数据，而不是只返回原始命令结果

## 目录

- `app/`: 应用主体
- `scripts/`: 调试脚本
- `tests/`: 单元测试与示例 fixture
- `config.example.json`: 配置样例
- `requirements.txt`: Python 依赖

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

接口启动时会先执行一次预热刷新，便于前端和 `/docs` 尽快拿到数据。
