# 项目结构说明

## 总体分层

项目分为三个主要部分：

- `backend`
  - 负责 SSH 查询、解析、轮询、缓存和接口输出
- `frontend`
  - 负责展示快照、处理导航和实时更新
- `Documents`
  - 负责记录项目说明、阶段目标和协作约定

## 当前后端结构

- `api`
  - 对外提供 REST 和 WebSocket
- `core`
  - 管理配置和共享状态
- `schemas`
  - 统一定义数据模型
- `services`
  - 负责轮询和业务数据组装
- `ssh`
  - 定义命令、执行 SSH、解析输出

## 当前前端结构

- `components/app`
  - 顶栏、侧栏等骨架组件
- `components/common`
  - 抽屉、空状态、调试面板等通用组件
- `store`
  - 快照状态和 WebSocket 生命周期
- `views`
  - Dashboard、Disks、Pools、Datasets

## 当前设计原则

- 状态真相源尽量在后端
- 前端优先做展示，不做重业务拼装
- 文档要跟着阶段实现同步更新
