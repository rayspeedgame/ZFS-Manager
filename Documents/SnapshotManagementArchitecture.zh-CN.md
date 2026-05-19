# Snapshot Management Architecture

> [English Version](./SnapshotManagementArchitecture.md)

## 当前基线

快照模块目前采用双入口结构：

- `DatasetsView` 负责快速手动创建快照
- `SnapshotsView` 负责集中管理快照

这套基线现在已经实现，并继续扩展到了：

- 手动快照创建与删除
- 支持高级模式的快照回滚
- 独立快照列表筛选与分页
- 定时快照工作流
- 快照保留清理

## 命名与归属规则

项目现在不再把“很长的快照名称”当作主要归属信号。

当前方向：

- 定时快照使用短命名：
  - `scheduled-{timestamp}-{random}`
- 计划身份通过 ZFS 用户属性记录
- 快照清理通过读取属性匹配计划归属，而不是解析长名称

推荐写入的属性组：

- snapshot kind
- schedule id
- strategy name
- schedule level
- retention keep-latest count
- recursive flag
- trigger source

## 保留策略模型

当前保留策略刻意保持保守：

- 每条计划只清理自己创建的快照
- 清理按计划身份匹配
- 递归计划仍按“每个数据集”分别保留，不使用全局总数
- 手动快照绝不能被定时清理影响

## 定时级别

当前支持的定时快照级别：

- 分钟级
- 小时级
- 天级
- 周级
- 月级

建议的产品规则：

- 按级别明确创建计划
- 前端只展示该级别需要的字段
- 后端统一保存规范化后的 pattern

## 前端职责

- `DatasetsView`：手动快照快速发起
- `SnapshotsView`：手动管理、回滚、删除、查看
- `SchedulesView`：定时快照创建与保留设置

## 后端职责

- 在定时快照创建时写入 ZFS 用户属性
- 在读取快照时从属性恢复计划归属
- 始终让保留清理只作用于创建这些快照的计划
- 避免依赖高风险、路径过重的快照命名

## 下一步

- 在更多快照界面中展示计划归属字段
- 支持编辑已有快照计划
- 在引入更复杂的分层保留之前，先增强保留策略报告
