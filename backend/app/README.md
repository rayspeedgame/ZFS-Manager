# app

`app/` 是后端主代码目录，负责配置加载、认证、接口暴露、SSH 查询、状态轮询、写操作执行和快照输出。

## 子目录职责

- `api/`: REST 和 WebSocket 路由
- `core/`: 配置、认证、共享状态等基础设施
- `schemas/`: Pydantic 数据模型
- `services/`: 轮询器、聚合器和写操作服务
- `ssh/`: SSH 命令定义、客户端和解析器

## 运行主线

- `main.py` 创建 FastAPI 应用，并在生命周期里启动 runtime
- runtime 持有当前配置和一组长生命周期服务
- `StatePoller` 负责按计划刷新各类状态并写入 `state_store`
- 写接口执行命令后统一触发一次强制刷新
- 设置接口保存后会重建 runtime，让新的配置立即生效
