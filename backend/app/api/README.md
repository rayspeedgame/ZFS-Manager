# api

这一层负责把后端内存中的最新快照暴露给前端。

## 文件说明

- `rest.py`: HTTP 接口，适合页面初始化和调试
- `ws.py`: WebSocket 推送，适合前端实时更新

## 当前约定

- REST 返回 JSON 快照
- WebSocket 使用 `send_json()` 推送完整快照
- 前端需要区分两种状态：
  - 浏览器到后端的 WebSocket 连接状态
  - 后端到 SSH 主机的 `source_status`
