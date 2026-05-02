# ZFS Manager

ZFS Manager 是一个面向家庭实验室和小型服务器环境的 ZFS 状态监控项目。后端通过 SSH 采集主机上的 `zpool`、`zfs`、`lsblk`、`blkid` 等信息，整理成稳定的结构化快照；前端通过 REST 和 WebSocket 读取这些快照并展示磁盘、池和数据集状态。

当前阶段已经完成的核心能力：

- 后端统一输出 `meta + data` 双层状态模型。
- SSH 采集失败时保留最近一次成功数据，并返回 `degraded` / `disconnected` 状态。
- 轮询已按 `pools`、`datasets`、`disks`、`properties` 解耦为不同频率。
- 前端直接消费后端整理后的 `summary`、`disks`、`pools`、`datasets`。
- 磁盘页支持展开分区信息，池页支持展开拓扑和分组属性查看。

## 目录

- `backend/`: FastAPI 后端、SSH 采集、状态轮询、解析与测试
- `frontend/`: Vue 3 + Vite 前端
- `Documents/`: 项目说明、阶段目标、Agent 说明

## 当前架构

数据流大致如下：

1. 后端 `StatePoller` 按计划执行 SSH 查询。
2. `parser` 将命令输出解析为结构化 overview。
3. `poller` 基于 overview 生成 `summary`、`disks`、`pools`、`datasets`。
4. 最新快照保存在内存中，并通过 REST / WebSocket 对外提供。
5. 前端根据 `snapshot.meta` 渲染连接和新鲜度状态，根据 `snapshot.data.*` 渲染页面。

## 快照模型

顶层快照分为两部分：

- `meta`: 采集状态、来源状态、错误、时间戳、陈旧时间、刷新计划
- `data`: 结构化业务数据和兼容保留的原始 overview

这样在 SSH 短暂失败时，前端仍能显示旧数据，同时明确告诉用户当前数据已陈旧。

## 运行方式

后端：

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 配置重点

后端配置见 `backend/config.example.json`。当前阶段与轮询相关的关键项包括：

- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`

推荐默认值已经写在示例配置中，适合作为当前阶段的起点。
