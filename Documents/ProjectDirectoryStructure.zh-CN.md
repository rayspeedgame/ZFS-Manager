# Project Directory Structure

> [English Version](./ProjectDirectoryStructure.md)

## 后端热点目录

- `backend/app/core/client_tracker.py`
  - 追踪已连接的 WebSocket 客户端数量
  - 驱动活跃↔空闲轮询模式在 ≤1 秒内切换
- `backend/app/services/poller.py`
  - 具备客户端感知的活跃/空闲刷新节奏的状态采集
  - 模式检测以固定 1 秒间隔运行；可配置的唤醒间隔仅控制刷新频率
  - 五个独立作业调度（disks、pools、datasets、properties、smart），每个都有独立的活跃和空闲间隔
  - 过滤 `loop`、`ram`、`fd`、`sr`、`zd`、`zram` 等非物理设备
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
  - 认证、设置、磁盘、Pool、Dataset、快照、任务和计划任务接口
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
- `backend/config/config.json`
  - 轮询、SSH、登录和磁盘自定义名称配置

## 部署入口

- `Dockerfile`
  - 使用 Node 构建前端，Python 镜像运行后端，并安装 Nginx
- `docker/start.sh`
  - 同时启动 Uvicorn 与 Nginx，并处理容器退出信号
- `docker/nginx.conf`
  - 提供 SPA 静态文件并代理 `/api/` 和 `/ws/`
- `compose.example.yaml`
  - 示例端口、环境变量和 `/data` 持久化卷

## 相关改动簇

- 客户端感知轮询
  - `backend/app/core/client_tracker.py`
  - `backend/app/services/poller.py`
  - `backend/app/api/ws.py`
  - `backend/app/core/config.py`
  - `frontend/src/views/SettingsView.vue`
- SMART 健康监控
  - `backend/app/ssh/commands.py` — `SMART_INFO` 命令
  - `backend/app/ssh/parser.py` — `parse_smartctl_output`、`parse_smart_info`
  - `backend/app/schemas/zfs_state.py` — `SmartOverview`、`DiskSmartInfo`、`SmartAttributeItem`
  - `backend/app/services/poller.py` — smart 调度、缓存、状态组装
  - `backend/app/api/routes/disks.py` — `GET /api/disks/{key}/smart`、`POST /api/disks/{key}/smart/refresh`
  - `backend/app/core/config.py` — smart 间隔设置
  - `frontend/src/views/DisksView.vue` — 健康列、SMART 详情弹窗
  - `frontend/src/views/SettingsView.vue` — 活跃/空闲 smart 间隔
  - `frontend/src/services/api.js` — `getDiskSmartData`、`refreshDiskSmartData`
  - `frontend/src/i18n/messages/*/disks.js` — SMART 翻译键
  - `backend/tests/fixtures/smart_info_sample.txt` — ATA + NVMe 解析/调试样例（当前自动化测试与 fixture poller 尚未加载）
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
