# Documents

> [English Version](./README.md)

`Documents/` 目录存放面向项目的设计、结构说明和开发路线文档。

## 文件索引

- `agent.md`: 面向后续开发者或代理的实现说明与扩展提示
- `target.md`: 产品目标与当前实现方向
- `Roadmap.md`: 功能路线图与推荐开发顺序
- `TaskSystemArchitecture.md`: 任务持久化、恢复与扩展性设计
- `ProjectStruction.md`: 项目高层结构概览
- `ProjectDirectoryStructure.md`: 按目录展开的代码结构说明

## 备注

- 运行时配置位于 `backend/config/`
- 后端行为主要围绕 SSH 轮询、REST 写操作和状态刷新展开
- 前端行为主要围绕视图、状态管理、API 服务和实时状态消费展开
- 任务系统设计默认将远端 ZFS 状态视为恢复时的主真相源
