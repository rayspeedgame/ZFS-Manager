# api

> [English Version](./README.md)

这一层向前端暴露 HTTP 和 WebSocket 接口。当前已经从单个超长
`rest.py` 拆成了按资源划分的路由模块，同时继续保留 `app.api.rest`
作为 `app.main` 使用的稳定聚合入口。

## 文件说明

- `rest.py`：聚合所有 HTTP 路由，作为稳定导入入口
- `ws.py`：向前端推送实时更新的 WebSocket 接口
- `common.py`：写操作路由共用的任务消息和命令日志辅助函数
- `constants.py`：REST 校验使用的数据集属性白名单
- `validators.py`：共用的 REST 校验与资源查找辅助函数
- `routes/system.py`：状态、认证、设置、SSH 测试、健康检查接口
- `routes/tasks.py`：任务记录和计划任务接口
- `routes/pools.py`：存储池创建、销毁、移除、属性、拓扑、scrub 接口
- `routes/datasets.py`：数据集创建、销毁、属性修改接口
- `routes/snapshots.py`：快照列表、筛选、详情、创建、删除、回滚接口

## 当前接口约定

- `GET /api/state`：返回完整应用快照
- `POST /api/state/refresh`：触发一次完整后端刷新
- `GET /api/auth/status`：返回是否启用登录以及当前请求是否已认证
- `POST /api/auth/login`：登录
- `POST /api/auth/logout`：登出
- `GET /api/settings`：读取当前生效配置
- `PUT /api/settings`：保存配置并热重载运行时
- `POST /api/settings/test-ssh`：在不保存配置的情况下测试 SSH 连通性
- `GET /api/tasks`：分页列出任务记录
  - 支持 `page`、`page_size`、`status_filter`
- `GET /api/tasks/{task_id}`：返回单条任务详情
- `GET /api/task-schedules`：列出计划任务
- `POST /api/task-schedules`：创建计划任务
- `PATCH /api/task-schedules/{schedule_id}`：更新计划任务
- `DELETE /api/task-schedules/{schedule_id}`：删除计划任务
- `POST /api/pools`：创建存储池
- `POST /api/pools/{pool_name}/destroy`：销毁存储池
- `POST /api/pools/{pool_name}/remove`：移除可删除的拓扑目标
- `POST /api/pools/{pool_name}/properties`：修改存储池属性
- `POST /api/pools/{pool_name}/topology`：添加支持的拓扑设备
- `POST /api/pools/{pool_name}/scrub/start`：启动 scrub
- `POST /api/pools/{pool_name}/scrub/stop`：停止 scrub
- `POST /api/datasets`：创建数据集或 zvol
- `POST /api/datasets/{dataset_name:path}/destroy`：销毁数据集
- `POST /api/datasets/{dataset_name:path}/properties`：修改数据集属性
- `GET /api/snapshots`：分页并按条件列出快照
- `GET /api/snapshots/filters`：返回快照筛选项
- `GET /api/snapshots/{snapshot_name:path}`：返回单个快照详情
- `GET /api/datasets/{dataset_name:path}/snapshots`：返回指定数据集的最近快照
- `POST /api/datasets/{dataset_name:path}/snapshots`：创建快照
- `DELETE /api/snapshots/{snapshot_name:path}`：删除快照
- `POST /api/snapshots/{snapshot_name:path}/rollback`：回滚快照

## 设计说明

- 数据集和快照名称使用 `{name:path}` 参数，这样 `tank/data`、
  `tank/data@snap-1` 这类多级名称可以直接工作。
- 除公开引导接口外，所有 `/api/*` 请求仍然会经过 `app.main`
  中的认证中间件。
- `OPTIONS` 预检请求被显式放行，避免浏览器携带凭证的跨域请求先被
  错误拦截成 `401`。
- 所有写操作在命令执行后仍会主动刷新一次状态，让前端看到的是主机
  的真实结果，而不是本地假设。
- `scrub` 这类长时间 pool 侧任务在启动成功后，会交回任务恢复层继续
  跟踪进度和最终状态。
