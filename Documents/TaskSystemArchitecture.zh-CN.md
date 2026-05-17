# Task System Architecture

> [English Version](./TaskSystemArchitecture.md)

## 目标

- 用一套任务系统统一承载写操作、长任务和计划任务
- 在本地持久化运维可见历史
- 在后端重启后恢复未完成工作流
- 让 ZFS 和主机状态成为长任务进度恢复的主真相源
- 为 `scrub`、`replace`、`expansion`、定时快照和未来工作流预留清晰扩展点

## 当前已落地形态

- 内存运行态任务管理器 + `SQLite` 任务存储
- 启动时重新加载任务并对活动任务做状态对账
- 基于 `zpool status` 的 `scrub` 恢复
- 面向按周定时 `scrub` 的计划任务持久化与后台调度
- 支持分页和状态筛选的任务记录页面

## 真相源分层

使用三层真相源，并明确各自职责：

1. 当前主机与 ZFS 状态
   - `zpool status`
   - `zpool list`
   - `zfs list`
   - `zfs get`
2. 事件与历史来源
   - `zpool history`
   - 未来如有需要，可继续接入主机日志或事件钩子
3. 本地应用记录
   - 任务表
   - 任务日志
   - 计划任务
   - 面向 UI 的标题、描述和元数据

系统不应把本地运行内存当成唯一真相源。

## 恢复模式

- `pool_scan_based`
  - 典型示例：`scrub`、`replace/resilver`、部分扩容场景
- `state_reconcile_based`
  - 典型示例：快照创建/删除、属性修改、创建/销毁操作
- `scheduler_based`
  - 典型示例：定时 `scrub`、定时快照
- `app_only`
  - 典型示例：未来没有主机侧对应状态的 UI 内部流程

## 存储模型

`SQLite` 仍然是当前阶段的默认且推荐选择，因为它：

- 部署简单
- 对单机应用足够稳定
- 足以承载任务历史、计划任务和审计友好的日志
- 后续如需扩展到多实例，也便于迁移

推荐的数据形态：

- `tasks`
  - 任务标识、类型、作用域、状态、进度、时间戳、元数据
- `task_logs`
  - 命令执行与输出记录
- `task_events`
  - 后续扩展更丰富的时间线
- `task_schedules`
  - 周期计划定义

## 当前运行流程

### 写操作驱动的任务

1. REST 写接口先验证请求
2. 创建任务并标记为运行中
3. 通过 SSH 执行实际命令
4. 后端强制刷新真实状态
5. 最后完成任务或更新任务

### 计划任务

1. 计划定义先持久化到本地
2. 后台调度器检查是否到期
3. 到期后调度器触发同一套底层工作流
4. 实际执行仍然登记为普通任务记录

### 启动恢复

1. 加载最近持久化任务
2. 采集一份新的基础状态快照
3. 将未完成任务与当前状态对账
4. 启动后台轮询和调度器

## 当前前端形态

- `TasksView.vue`
  - 展示任务记录和状态
  - 支持分页、每页条数调整和状态筛选
  - 当前筛选结果为空时仍保留完整页面框架和筛选控件
- `SchedulesView.vue`
  - 管理定时 `scrub`
  - 为未来快照计划预留占位区域
- `PoolDetailDrawer.vue`
  - 暴露 `scrub` 控制入口和当前扫描状态

## 当前 API 面

- `GET /api/tasks`
  - 支持 `page`、`page_size` 和 `status_filter`
- `GET /api/tasks/{task_id}`
- `GET /api/task-schedules`
- `POST /api/task-schedules`
- `PATCH /api/task-schedules/{schedule_id}`
- `DELETE /api/task-schedules/{schedule_id}`
- `POST /api/pools/{pool_name}/scrub/start`
- `POST /api/pools/{pool_name}/scrub/stop`

## 扩展性建议

- 恢复器继续使用可注册模式，而不是堆叠在单个 `if/else` 中
- 计划任务继续走同一套任务系统，不要单独旁路
- 把运维可见元数据和主机真实状态分层保存
- 在当前状态筛选之外，为后续按任务类型筛选预留空间
- 允许未来识别“由外部发起但当前 UI 需要展示”的任务，例如主机侧直接启动的 `scrub`

## 紧接着的扩展方向

1. 定时快照与保留策略
2. `replace/resilver` 恢复器
3. 更细的事件表和日志表
4. 可选的后台活动任务持续对账，让任务页未打开时也能持续更新活动任务
