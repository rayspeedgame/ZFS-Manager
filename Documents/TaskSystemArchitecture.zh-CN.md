# Task System Architecture

> [English Version](./TaskSystemArchitecture.md)

## 目标

- 将写操作、长时间任务和计划任务统一纳入一套任务系统
- 在本地持久化面向运维的历史记录
- 在后端重启后恢复未完成工作
- 让长时间任务的真实状态尽量来自 ZFS 和主机状态
- 为 `scrub`、定时快照、保留策略、`replace` 和后续能力预留清晰扩展点

## 当前已交付形态

- 运行时任务管理器加 SQLite 持久化
- 启动任务回填与活动任务对账
- 基于 `zpool status` 的 `scrub` 恢复
- 计划任务持久化与后台调度
- 定时 `scrub`
- 定时 `snapshot`
- 按计划归属执行的快照保留清理
- 支持分页和状态筛选的任务记录页面

## 真实来源分层

使用三层来源，并保持职责清晰：

1. 主机与 ZFS 当前状态
   - `zpool status`
   - `zpool list`
   - `zfs list`
   - `zfs get`
2. 事件与历史来源
   - `zpool history`
   - 未来的主机日志或事件钩子
3. 本地应用记录
   - task 行
   - task schedule 行
   - task log
   - 面向运维的附加元数据

## 当前定时快照规则

- 定时快照使用短格式名称
- 归属与保留身份通过 ZFS 用户属性写入
- 清理逻辑按计划身份匹配快照
- 递归计划仍按每个数据集分别保留，而不是按全局总数

## 当前前端形态

- `TasksView.vue`
  - 分页任务记录与状态筛选
- `SchedulesView.vue`
  - 定时 `scrub`
  - 定时 `snapshot`
  - 统一的站内删除确认弹窗
- `SnapshotsView.vue`
  - 集中快照管理与回滚

## 下一步

1. 支持编辑已有快照计划
2. 增强保留策略报告
3. 增加 `replace/resilver` 恢复器
4. 即使任务页未打开，也在后台持续更新活动任务对账
