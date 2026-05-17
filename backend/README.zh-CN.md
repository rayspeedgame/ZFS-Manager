# Backend

> [English Version](./README.md)

后端当前主要负责五件事：采集远端主机状态、整理统一快照、执行 ZFS/ZPool 写操作、持久化运维可见任务，以及在重启后恢复未完成工作流。

## 主要职责

- 通过 SSH 执行只读命令，采集：
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status/list/get`
  - `zfs list/get`
- 将原始命令输出整理为统一的 `meta + data` 快照
- 暴露 REST 接口：
  - 状态读取与强制刷新
  - 设置读取、保存与 SSH 测试
  - 登录状态、登录、退出
  - pool 和 dataset 写操作
  - `scrub` 启动与停止
  - 任务列表、任务详情和计划任务接口
- 通过 WebSocket 推送最新快照
- 使用 `SQLite` 持久化任务与计划任务，并在启动时对未完成工作流做恢复对账

## 目录说明

- `app/api/`
  - REST 和 WebSocket 入口
- `app/core/`
  - 配置、认证、共享状态和运行时基础设施
- `app/schemas/`
  - Pydantic 请求、响应、快照、任务和计划任务模型
- `app/services/`
  - 轮询、状态聚合、写操作、任务、计划任务与恢复逻辑
- `app/ssh/`
  - SSH 客户端、命令定义和解析器
- `config/`
  - 当前使用的配置目录，以及 `tasks.sqlite3`
- `tests/fixtures/`
  - fixture 模式输入样例

## 当前实现重点

- `StatePoller` 按 `pools / datasets / disks / properties` 分频刷新
- 写操作完成后仍统一调用 `poller.refresh_once(force_all=True)`
- `TaskManager + SQLiteTaskStore`
  - 组合形成“内存运行态 + SQLite 持久化”的任务系统
- `TaskRecoveryService`
  - 在启动时和读取任务时对未完成任务做状态对账
- `TaskScheduler`
  - 持久化并执行周期性的 `scrub` 计划
- `poller.py`
  - 已为每个 pool 生成结构化 `scanStatus`
- 认证采用轻量 cookie 登录，默认关闭，可由设置页启用

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
