# store

这里负责前端全局状态、快照缓存和 WebSocket 生命周期。

## 当前重点

- 维护浏览器到后端的连接状态
- 接收 WebSocket 推送的最新快照
- 提供 `refreshStateOnce()` 主动拉取最新状态
- 提供 `updatePoolProperties()` 提交 pool 属性修改

## 关键区分

前端 store 中的 WebSocket 状态不等于后端 SSH 数据源状态。页面需要同时读取：

- 传输层状态
- `snapshot.meta` 中的应用状态与来源状态
