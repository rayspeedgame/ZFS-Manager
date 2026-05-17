# stores

> [English Version](./README.md)

Pinia store 放在这里。

## 文件

- `app.js`
  - WebSocket 生命周期
  - 快照缓存
  - 认证状态
  - 登录、退出和刷新动作
- `tasks.js`
  - 任务记录缓存
  - 选中任务详情
  - 分页状态
  - 状态筛选状态
  - 周期刷新逻辑

## 说明

- 这些 store 替代了更早期的单例式前端状态实现
- 开启登录门禁时，app store 会在认证成功后再建立 WebSocket 连接
- tasks store 现在还负责在刷新过程中保持任务页交互状态稳定
