# Project Directory Structure

> [English Version](./ProjectDirectoryStructure.md)

## 后端热点目录

- `backend/app/core/client_tracker.py`
  - 追踪已连接的 WebSocket 客户端数量
  - 驱动活跃↔空闲轮询模式在 ≤1 秒内切换
- `backend/app/services/poller.py`
  - 具备客户端感知的活跃/空闲刷新节奏的状态采集
  - 模式检测以固定 1 秒间隔运行；可配置的唤醒间隔仅控制刷新频率
  - 四个独立作业调度，每个都有独立的活跃和空闲间隔
- `backend/app/services/task_scheduler.py`
  - 周期任务调度器
  - 执行定时 `scrub`
  - 执行定时 `snapshot`
  - 协调按计划范围执行的快照保留清理
- `backend/app/services/snapshot_metadata.py`
  - 定义写入定时快照的 ZFS 用户属性键
- `backend/app/services/snapshot_retention.py`
  - 生成短格式定时快照名
  - 按数据集分组清理同计划归属的快照
- `backend/app/services/snapshot_creator.py`
  - 通过 `zfs snapshot -o` 写入定时快照用户属性
- `backend/app/services/snapshot_query.py`
  - 从快照属性中读回计划归属信息
- `backend/app/schemas/task_schedule.py`
  - 统一的周期 pattern 模型

## 前端热点目录

- `frontend/src/components/common/HelpTooltip.vue`
  - 属性 `?` 帮助图标，hover 时出现说明弹出框
- `frontend/src/views/SnapshotsView.vue`
  - 独立快照管理页面，负责筛选、删除、回滚和详情抽屉
- `frontend/src/views/SchedulesView.vue`
  - 周期任务页面，负责定时 `scrub` 与定时 `snapshot`
  - 支持分钟级、小时级、天级、周级、月级快照计划
- `frontend/src/views/TasksView.vue`
  - 任务记录与状态页面，支持分页和状态筛选
- `frontend/src/views/DatasetsView.vue`
  - 数据集树与手动快照快速创建入口
- `frontend/src/services/api.js`
  - 快照接口、任务接口、计划任务接口
- `frontend/src/views/SettingsView.vue`
  - 活跃与空闲轮询间隔配置
  - 空闲刷新子区域，包含各项独立的空闲间隔设置

## 持久化与恢复

- `backend/config/tasks.sqlite3`
  - 任务和计划任务的 SQLite 存储
- `backend/app/services/task_store.py`
  - 任务与计划任务持久化层
- `backend/app/services/task_recovery.py`
  - 启动恢复与任务对账

## 相关改动簇

- 客户端感知轮询
  - `backend/app/core/client_tracker.py`
  - `backend/app/services/poller.py`
  - `backend/app/api/ws.py`
  - `backend/app/core/config.py`
  - `frontend/src/views/SettingsView.vue`
- 快照管理
  - `backend/app/services/snapshot_creator.py`
  - `backend/app/services/snapshot_destroyer.py`
  - `backend/app/services/snapshot_rollbacker.py`
  - `backend/app/services/snapshot_query.py`
  - `frontend/src/views/SnapshotsView.vue`
- 定时快照与保留策略
  - `backend/app/services/task_scheduler.py`
  - `backend/app/services/snapshot_metadata.py`
  - `backend/app/services/snapshot_retention.py`
  - `backend/app/schemas/task_schedule.py`
  - `frontend/src/views/SchedulesView.vue`
- 任务系统
  - `backend/app/services/task_manager.py`
  - `backend/app/services/task_store.py`
  - `backend/app/services/task_recovery.py`
  - `frontend/src/stores/tasks.js`
  - `frontend/src/views/TasksView.vue`
