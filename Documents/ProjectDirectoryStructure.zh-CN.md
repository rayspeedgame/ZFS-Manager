# Project Directory Structure

> [English Version](./ProjectDirectoryStructure.md)

```text
ZFS-Manager/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- ssh/
|   |-- config/
|   |   |-- config.example.json
|   |   |-- config.json
|   |   `-- tasks.sqlite3
|   |-- scripts/
|   |-- tests/
|   |   `-- fixtures/
|   |-- README.md
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- app/
|   |   |   |-- common/
|   |   |   |-- datasets/
|   |   |   `-- pools/
|   |   |-- i18n/
|   |   |   `-- messages/
|   |   |       |-- en-US/
|   |   |       `-- zh-CN/
|   |   |-- lib/
|   |   |-- router/
|   |   |-- services/
|   |   |-- store/
|   |   |-- stores/
|   |   `-- views/
|   |-- README.md
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- Documents/
|   |-- README.md
|   |-- agent.md
|   |-- target.md
|   |-- Roadmap.md
|   |-- TaskSystemArchitecture.md
|   |-- ProjectStruction.md
|   `-- ProjectDirectoryStructure.md
`-- README.md
```

## 前端热点目录

- `frontend/src/views/TasksView.vue`
  - 任务记录和状态页面
  - 负责任务分页浏览、状态筛选、刷新和任务详情查看
- `frontend/src/views/SchedulesView.vue`
  - 计划任务页面
  - 当前负责定时 `scrub` 创建，以及定时快照占位区
- `frontend/src/views/PoolsView.vue`
  - pool 概览、拓扑、属性编辑和 `scrub` 操作
- `frontend/src/components/pools/PoolDetailDrawer.vue`
  - 池详情抽屉，包含 `scrub` 状态摘要、开始/停止按钮和属性编辑
- `frontend/src/stores/tasks.js`
  - 任务列表缓存、分页状态、状态筛选、选中项和自动刷新
- `frontend/src/services/api.js`
  - pool / dataset 写接口、任务接口、计划任务接口、认证接口和 `scrub` 接口
- `frontend/src/router/routes.js`
  - 仪表盘、磁盘、存储池、数据集、计划任务、任务记录和设置的导航元数据

## 后端热点目录

- `backend/config/tasks.sqlite3`
  - 任务与计划任务的 `SQLite` 数据库
- `backend/app/core/config.py`
  - 配置加载、保存，以及任务数据库路径解析
- `backend/app/services/task_store.py`
  - 基于 `SQLite` 的任务与计划任务持久化层
- `backend/app/services/task_manager.py`
  - 内存运行态任务管理器，已支持分页与状态筛选
- `backend/app/services/task_recovery.py`
  - 恢复注册表与活动任务对账服务
- `backend/app/services/task_scheduler.py`
  - 周期计划任务后台调度器
- `backend/app/services/pool_scrubber.py`
  - `zpool scrub` / `zpool scrub -s` 执行器
- `backend/app/schemas/pool_scrub.py`
  - `scrub` 请求/响应模型
- `backend/app/schemas/task_schedule.py`
  - 计划任务的创建、更新、列表和详情模型
- `backend/app/api/rest.py`
  - 状态、设置、认证、任务列表/详情、计划任务和 `scrub` 启停接口
- `backend/app/services/poller.py`
  - 为每个 pool 生成结构化 `scanStatus`

## 相关变更簇

- 任务系统
  - `backend/app/services/task_store.py`
  - `backend/app/services/task_manager.py`
  - `backend/app/services/task_recovery.py`
  - `backend/app/schemas/task.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
- 计划任务
  - `backend/app/services/task_scheduler.py`
  - `backend/app/schemas/task_schedule.py`
  - `backend/app/api/rest.py`
  - `frontend/src/views/SchedulesView.vue`
- Scrub
  - `backend/app/services/pool_scrubber.py`
  - `backend/app/schemas/pool_scrub.py`
  - `backend/app/api/rest.py`
  - `backend/app/services/poller.py`
  - `frontend/src/views/PoolsView.vue`
  - `frontend/src/components/pools/PoolDetailDrawer.vue`
- 配置与认证
  - `backend/app/core/config.py`
  - `backend/app/core/auth.py`
  - `backend/app/main.py`
