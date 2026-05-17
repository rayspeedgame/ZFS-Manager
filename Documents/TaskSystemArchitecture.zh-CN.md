# 任务记录与恢复系统设计

> [English Version](./TaskSystemArchitecture.md)

## 目标

本设计稿定义 ZFS Manager 的任务记录、持久化、恢复和展示体系。当前实现已经覆盖以下两层：

- 第一层：`SQLite` 持久化
- 第二层：启动恢复流程与恢复注册表

设计目标如下：

- 统一记录写操作、长时间任务和计划任务
- 后端重启后尽量恢复任务上下文，而不是只依赖进程内内存
- 以 ZFS / 系统自身可读取状态作为主要真相来源
- 为 `scrub`、`replace`、`expansion`、快照计划等能力预留稳定扩展点

## 当前实现状态

### 已落地

- `TaskManager`
  - 负责内存中的任务运行态
- `SQLiteTaskStore`
  - 负责任务主记录持久化
- `TaskRecoveryRegistry`
  - 负责恢复器注册
- `TaskRecoveryService`
  - 负责启动恢复和活动任务对账
- `scrub`
  - 已接入任务创建、任务恢复和进度恢复

### 当前边界

- 目前持久化的是任务主记录快照，还没有拆分出 `task_events` 和 `task_logs` 数据表
- 当前活动任务对账是在读取任务接口时触发，尚未完全并入后台轮询
- `scrub` 已具备基于 `zpool status` 的恢复逻辑
- `replace/resilver`、`expansion`、计划任务恢复器尚未完成

## 核心原则

### 1. 分层真相源

- `ZFS 当前状态`
  - 例如 `zpool status`、`zpool list`、`zfs list`、`zfs get`
- `ZFS / 系统历史事件`
  - 例如 `zpool history`
- `应用数据库`
  - 保存任务元数据、展示信息、日志聚合和筛选索引

### 2. 状态外部化，展示本地化

- 任务真实状态尽量通过远端系统重新探测
- 任务卡片、列表、日志和筛选索引由本地数据库维护

### 3. 按任务类型定义恢复策略

- `pool_scan_based`
  - 依赖 `zpool status`
  - 典型任务：`scrub`、`replace/resilver`、部分 expansion
- `state_reconcile_based`
  - 通过目标状态对账判断是否完成
  - 典型任务：快照创建、快照删除、属性修改
- `scheduler_based`
  - 调度计划由应用维护，执行结果再和 ZFS 状态对账
- `app_only`
  - 只能依赖应用记录恢复

## 当前架构

### 1. Task API

- `GET /api/tasks`
- `GET /api/tasks/{id}`
- 已在读取时触发活动任务对账

### 2. Task Store

- 当前为 `SQLiteTaskStore`
- 默认数据库路径：`backend/config/tasks.sqlite3`
- 可通过环境变量 `ZFS_MANAGER_TASK_DB` 覆盖

### 3. Task Runtime

- 当前由 `TaskManager` 维护
- 保存任务当前状态、进度、阶段、命令日志和元数据

### 4. Task Recovery Engine

- 当前由 `TaskRecoveryService` 负责
- 启动顺序：
  1. 加载 SQLite 中的最近任务
  2. 刷新一次远端状态
  3. 将未终态任务标记为 `recovering`
  4. 调用恢复器完成恢复判定

### 5. Task Source Adapters

- 当前已经依赖：
  - `zpool status`
  - `zpool list`
  - `zfs list`
  - `zfs get`

## 当前数据模型

当前 `SQLite` 已落地 `tasks` 表，保存：

- `id`
- `title`
- `kind`
- `scope_type`
- `scope_name`
- `status`
- `progress`
- `stage`
- `message`
- `created_at`
- `started_at`
- `finished_at`
- `command_logs_json`
- `metadata_json`
- `updated_at`

## 任务状态模型

当前任务系统已使用以下状态：

- `queued`
- `running`
- `recovering`
- `succeeded`
- `failed`
- `canceled`
- `unknown`
- `needs_attention`

## 恢复器设计

### 当前实现

- `KnownWriteTaskRecoveryHandler`
  - 处理当前已交付的写任务恢复
- `pool.scrub.start`
  - 已支持从 `zpool status` 的 `scan` 文本恢复为 `running / succeeded / canceled / unknown`
- `pool.scrub.stop`
  - 已支持根据当前是否仍有活动 scrub 进行恢复

### scrub 恢复方式

当前恢复逻辑基于 pool 的 `scan` 文本解析：

- `scrub in progress`
  - 恢复为 `running`
- `scrub repaired` / `scrub completed`
  - 恢复为 `succeeded`
- `scrub canceled` / `scrub stopped`
  - 恢复为 `canceled`

同时解析：

- 进度百分比
- ETA
- 当前原始扫描文本

这些信息会回写到任务记录中。

## 当前前后端联动

### 后端

- `pool_scrubber.py`
  - 负责执行 `zpool scrub` 和 `zpool scrub -s`
- `poller.py`
  - 为每个 pool 生成结构化 `scanStatus`
- `task_recovery.py`
  - 将 `scanStatus` / `scan` 用于恢复和对账

### 前端

- `PoolDetailDrawer.vue`
  - 展示 `scrub` 区块
  - 提供开始/停止按钮
  - 展示当前扫描文本、进度、ETA 和状态
- `TasksView.vue`
  - 持续展示 `scrub` 任务进度和日志

## 推荐下一步

- 将活动任务对账并入后台轮询
- 为 `replace/resilver` 增加 `pool_scan_based` 恢复器
- 拆分出 `task_events` 和 `task_logs` 表
- 增加 `task_schedules`
- 支持外部发现的活动任务

## 结论

当前任务系统已经从“纯内存可视化”进入“可持久化、可启动恢复、可承载长任务”的阶段。  
`scrub` 已经是第一类完整接入任务恢复体系的 pool 级长任务样板，后续其他长任务应沿用同样的架构模式继续扩展。
