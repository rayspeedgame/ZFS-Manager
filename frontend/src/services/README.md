# services

前端 API 服务层。

## Files

- `api.js`
  - pool、dataset 写请求
  - 设置读取、保存、SSH 测试
  - 登录状态、登录、退出
  - 共享 API 基础地址辅助函数

## Notes

- 所有请求默认携带 `credentials: "include"`，以便复用后端的登录 cookie
- 这一层负责把请求路径和 payload 形状与后端 API 对齐
