# app

`app/` 是后端主代码目录，负责配置加载、接口暴露、SSH 查询、状态轮询、数据解析与快照输出。

## 子目录职责

- `api/`: REST 与 WebSocket 路由
- `core/`: 配置、共享状态等基础能力
- `schemas/`: Pydantic 数据模型
- `services/`: 轮询、聚合和发布逻辑
- `ssh/`: SSH 命令定义、客户端和解析器

## 运行主线

`main.py` 创建 FastAPI 应用，并在生命周期中启动 `StatePoller`。  
`StatePoller` 负责按不同频率刷新各类数据，组装快照后写入共享状态，再通过接口提供给前端。
