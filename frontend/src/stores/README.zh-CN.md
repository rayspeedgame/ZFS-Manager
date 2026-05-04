# stores

> [English Version](./README.md)

Pinia store 放在这里。

## Files

- `app.js`
  - WebSocket 生命周期
  - 快照缓存
  - 认证状态
  - 登录、退出、刷新动作

## Notes

- 这个 store 替代了旧的模块单例状态实现
- 登录门禁开启时，store 会在认证通过后再建立 WebSocket 连接
