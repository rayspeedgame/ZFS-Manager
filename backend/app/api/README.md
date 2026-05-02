# api

这一层负责把后端内存中的最新快照和控制接口暴露给前端。

## 文件说明

- `rest.py`: HTTP 接口，提供状态读取、健康检查和池属性写回
- `ws.py`: WebSocket 推送，适合前端实时更新

## 当前约定

- `GET /api/state` 返回完整 JSON 快照
- `POST /api/pools/{pool_name}/properties` 接收本次变更列表，并按属性逐项返回执行结果
- `POST /api/pools/{pool_name}/topology` 接收本次拓扑新增列表，并按操作逐项返回执行结果
- 属性写回完成后，后端会主动触发一次刷新，尽快把最新状态推回前端
- WebSocket 使用 `send_json()` 推送完整快照
