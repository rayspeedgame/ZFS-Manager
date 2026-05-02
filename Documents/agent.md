# Agent Guide

## 项目定位

ZFS Manager 是一个通过 SSH 采集远端 ZFS 主机状态，并以 Web 界面展示和管理的项目。当前阶段已经从只读监控进入“有限写回”阶段，支持修改部分 pool 属性并查看执行结果。

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

修改功能时，应继续保持这套分层，不要把状态字段和业务数据重新混在一起。

## 当前业务约定

### 后端

- 轮询任务按 `pools`、`datasets`、`disks`、`properties` 分频执行
- 属性写回使用独立接口，不直接手改快照，而是执行命令后强制刷新
- 写回结果按属性逐项返回，允许部分成功、部分失败

### 前端

- 顶栏区分 WebSocket 状态和 SSH 来源状态
- Pools 详情页支持：
  - 只读属性与可编辑属性分组
  - 保存前确认
  - 保存中状态展示
  - 逐项结果列表
  - SSH Terminal Log

## 编码约定

- 在关键逻辑处加入简洁注释，帮助快速理解意图
- 注释应解释“为什么这样做”或“这段逻辑负责什么”
- 不要添加逐行翻译式注释，也不要堆砌显而易见的说明

## 修改建议

- 优先让后端产出稳定数据，再让前端消费
- 新增字段时，优先扩展 `data.*` 领域模型
- 涉及性能问题时，优先减少不必要的深层监听、重复计算和大对象序列化
- 涉及 UI 状态表达时，注意区分“连接层异常”和“数据源异常”

## 后续方向

- 接入 SMART 信息
- 扩展 dataset 可写属性能力
- 继续细化属性分组和多语言支持
