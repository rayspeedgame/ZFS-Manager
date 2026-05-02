# app

`app/` 是后端主代码目录，负责配置加载、接口暴露、SSH 查询、状态轮询、属性写回和快照输出。

## 子目录职责

- `api/`: REST 与 WebSocket 路由
- `core/`: 配置、共享状态等基础能力
- `schemas/`: Pydantic 数据模型
- `services/`: 轮询、聚合和属性写回服务
- `ssh/`: SSH 命令定义、客户端和解析器

## 运行主线

- `main.py` 创建 FastAPI 应用，并在生命周期中启动 `StatePoller`
- `StatePoller` 负责按不同频率刷新各类状态并写入 `state_store`
- 写回接口调用 `property_updater` 执行命令，再调用 `poller.refresh_once(force_all=True)` 强制刷新
