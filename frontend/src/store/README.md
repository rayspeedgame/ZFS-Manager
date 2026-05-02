# store

这里负责前端全局状态、快照缓存和 WebSocket 生命周期。

## 当前重点

- 维护浏览器到后端的连接状态
- 接收 REST / WebSocket 快照
- 暴露当前 `snapshot`

## 关键区分

前端 store 中的 WebSocket 状态不等于后端 SSH 来源状态。  
页面需要同时读取：

- 传输层状态
- `snapshot.meta` 中的应用与来源状态
