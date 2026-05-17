# Documents

> [English Version](./README.md)

`Documents/` 目录存放面向项目的设计说明、结构说明和开发路线文档。

## 文档索引

- `agent.md`：面向后续开发者或代理的实现说明与扩展提示
- `target.md`：产品目标与当前已交付能力概览
- `Roadmap.md`：功能路线图、开发顺序与下一阶段重点
- `TaskSystemArchitecture.md`：任务持久化、恢复、调度与扩展性设计
- `ProjectStruction.md`：项目高层结构概览
- `ProjectDirectoryStructure.md`：按目录展开的代码结构说明

## 当前备注

- 运行时配置位于 `backend/config/`
- 后端当前围绕 SSH 轮询、REST 写操作、任务持久化与恢复展开
- 前端当前围绕路由视图、Pinia 状态、i18n 和实时快照消费展开
- 任务系统目前已经覆盖：
  - `SQLite` 持久化任务历史
  - 启动恢复
  - 定时 `scrub` 计划
  - 可分页、可按状态筛选的任务记录
- 长任务恢复仍以 ZFS 和主机真实状态作为主真相源
