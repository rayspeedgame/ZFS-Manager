# app

> [English Version](./README.md)

`app/` 是后端主代码目录，负责配置加载、认证、接口暴露、SSH 查询、状态轮询、写操作执行和快照输出。

## 子目录职责

- `api/`: REST 和 WebSocket 路由
- `core/`: 配置、认证、客户端跟踪和共享状态等基础设施
- `schemas/`: Pydantic 数据模型，包含状态、写请求、任务、计划和 SMART 模型
- `services/`: 轮询器、聚合器、写操作、任务持久化/恢复和调度服务
- `ssh/`: SSH 命令定义、客户端和解析器（含 `SMART_INFO` 与 `smartctl --json`）

## 运行主线

- `main.py` 创建 FastAPI 应用，并在生命周期里启动 runtime
- runtime 持有当前配置和一组长生命周期服务
- `StatePoller` 负责按计划刷新各类状态并写入 `state_store`
- 写接口执行命令后统一触发一次强制刷新
- 设置接口保存后会重建 runtime，让新的配置立即生效
- runtime 启动时会恢复未完成任务并启动计划调度器；任务接口访问时也会触发一次恢复检查
