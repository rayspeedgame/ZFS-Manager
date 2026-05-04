# api

> [English Version](./README.md)

这一层负责把后端内存中的最新快照和控制接口暴露给前端。

## 文件说明

- `rest.py`: HTTP 接口，提供状态读取、设置管理、认证和写操作入口
- `ws.py`: WebSocket 推送，用于前端实时更新

## 当前接口约定

- `GET /api/state`: 返回完整应用快照
- `POST /api/state/refresh`: 触发一次全量后端刷新
- `GET /api/settings`: 读取当前生效配置
- `PUT /api/settings`: 保存配置并热重载 runtime
- `POST /api/settings/test-ssh`: 用临时参数测试 SSH 连接，不保存配置
- `GET /api/auth/status`: 返回是否启用登录，以及当前是否已认证
- `POST /api/auth/login`: 登录
- `POST /api/auth/logout`: 退出登录
- `POST /api/pools/{pool_name}/properties`: 修改 pool 属性
- `POST /api/pools/{pool_name}/topology`: 新增 topology 设备
- `POST /api/pools`: 创建 pool
- `POST /api/pools/{pool_name}/destroy`: 删除 pool
- `POST /api/pools/{pool_name}/remove`: 移除可删除 topology 目标
- `POST /api/datasets`: 创建 dataset / zvol
- `POST /api/datasets/{dataset_name:path}/properties`: 修改 dataset 属性
- `POST /api/datasets/{dataset_name:path}/destroy`: 删除 dataset

## 当前约束

- dataset 路由使用 `{dataset_name:path}`，以支持 `tank/data` 这类多级名称
- 除公开接口外，其余 `/api/*` 请求都需要通过认证中间件
- 写操作完成后会主动刷新，尽快把真实主机状态推回前端
