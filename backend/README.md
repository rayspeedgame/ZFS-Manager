# Backend

后端使用 FastAPI 提供 REST 和 WebSocket 接口，并通过 SSH 轮询远端 ZFS 主机状态。

## 当前阶段重点

- 输出统一的 `meta + data` 快照
- 轮询任务按 `pools`、`datasets`、`disks`、`properties` 分频执行
- 失败时保留最近一次成功快照
- 提供 pool 属性写回接口
- 写回完成后强制刷新一次最新状态

## 目录

- `app/`: 应用主体
- `scripts/`: 调试脚本
- `tests/`: 单元测试与 fixture
- `config.example.json`: 配置样例
- `requirements.txt`: Python 依赖

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
