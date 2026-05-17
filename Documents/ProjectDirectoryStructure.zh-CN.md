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

## 前端说明

- `frontend/src/views/TasksView.vue`
  - 最近写操作和长任务的统一任务页
- `frontend/src/views/PoolsView.vue`
  - pool 概览、拓扑、属性编辑，以及 `scrub` 入口
- `frontend/src/components/pools/PoolDetailDrawer.vue`
  - 池详情抽屉，包含 `scrub` 状态、开始/停止按钮和属性编辑
- `frontend/src/stores/tasks.js`
  - 任务列表、详情和自动刷新
- `frontend/src/services/api.js`
  - 包含 pool / dataset 写接口、任务接口、以及 `scrub` 接口

## 后端说明

- `backend/config/tasks.sqlite3`
  - 当前任务持久化数据库
- `backend/app/core/config.py`
  - 配置加载、保存，以及任务数据库路径解析
- `backend/app/services/task_store.py`
  - `SQLite` 任务持久化层
- `backend/app/services/task_manager.py`
  - 内存运行态任务管理器
- `backend/app/services/task_recovery.py`
  - 任务恢复注册表和恢复服务
- `backend/app/services/pool_scrubber.py`
  - `zpool scrub` / `zpool scrub -s` 执行器
- `backend/app/schemas/pool_scrub.py`
  - `scrub` 请求响应模型
- `backend/app/api/rest.py`
  - 状态、设置、认证、任务接口，以及 `scrub` 启停接口
- `backend/app/services/poller.py`
  - 为每个 pool 生成结构化 `scanStatus`

## 相关热点

- 任务系统
  - `backend/app/services/task_store.py`
  - `backend/app/services/task_manager.py`
  - `backend/app/services/task_recovery.py`
  - `backend/app/schemas/task.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
- scrub
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
