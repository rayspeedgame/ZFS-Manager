# Documents

> [English Version](./README.md)

`Documents/` 用来存放项目级设计文档、开发路线图和代码结构说明。

## 索引

- `agent.md`：交接说明、实现约定和扩展提示
- `target.md`：产品目标与当前已交付能力
- `Roadmap.md`：开发路线图与下一阶段重点
- `TaskSystemArchitecture.md`：任务持久化、恢复、调度与扩展性设计
- `SnapshotManagementArchitecture.md`：快照模块结构、独立页面设计、定时快照与保留策略方向
- `ProjectStruction.md`：项目高层结构说明
- `ProjectDirectoryStructure.md`：按目录展开的代码地图

## 当前重点

- 后端采用 SSH 轮询加 REST 写操作模式
- 任务系统目前已经包含：
  - 基于 SQLite 的任务与计划任务持久化
  - 启动恢复与活动任务对账
  - 定时 `scrub`
  - 定时 `snapshot`
  - 基于计划范围的快照保留清理
- 快照模块目前已经包含：
  - 数据集页面快速创建入口
  - 独立快照页面
  - 回滚流程
  - 高级回滚模式选择
  - 从分钟到月的定时快照
  - 基于 ZFS 用户属性的定时快照归属与保留标记

## 说明

- 运行时配置位于 `backend/config/`
- 长时间任务的真实状态应尽量来自 ZFS 和主机状态本身
- 定时快照的清理匹配现在依赖写入快照用户属性的计划元数据，而不是依赖很长的快照名称
