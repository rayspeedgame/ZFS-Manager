# Agent Guide

## 项目定位

ZFS Manager 是一个通过 SSH 采集远端 ZFS 主机状态，并以 Web 界面展示的管理与监控项目。当前更偏“状态观测与结构化展示”，尚未进入大规模编辑和控制阶段。

## 当前架构摘要

- 后端：FastAPI + asyncssh + Pydantic
- 前端：Vue 3 + Vite
- 传输：REST + WebSocket，统一使用 JSON

## 当前状态模型

后端快照分为：

- `meta`
  - `app_status`
  - `source_status`
  - `message`
  - `last_attempt_at`
  - `last_success_at`
  - `stale_seconds`
  - `refresh_plan_seconds`
- `data`
  - `summary`
  - `disks`
  - `pools`
  - `datasets`
  - 兼容保留的 overview

Agent 在修改功能时，应优先保持这个分层，不要重新把状态和业务数据揉回一起。

## 当前业务约定

### 后端

- 失败时保留最近一次成功数据
- 轮询已按 `pools`、`datasets`、`disks`、`properties` 解耦
- 多 pool 场景下，磁盘归属依赖 `zpool status` 拓扑映射

### 前端

- 顶栏区分 WebSocket 状态与 SSH 来源状态
- Dashboard 第一张卡为 `Disks`
- Disks 页支持展开分区
- Pools 页支持：
  - 行展开查看拓扑与额外参数
  - 抽屉查看属性
  - 只读属性高级展开

## 修改建议

- 优先让后端产出稳定数据，再让前端消费
- 新增字段时，优先扩展 `data.*` 领域模型
- 若涉及性能问题，优先考虑刷新频率和数据范围，而不是先改传输格式
- 若涉及 UI 状态表达，注意区分“传输层断开”和“SSH 来源异常”

## 后续方向

- 接入 SMART 信息
- 继续细化池与数据集属性分类
- 视需要加入可修改参数的写回能力
