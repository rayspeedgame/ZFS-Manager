# ZFS Manager

ZFS Manager 是一个通过 SSH 采集远端 ZFS 主机状态，并通过 Web 页面展示与管理的项目。当前阶段已经从“只读监控”推进到“有限属性写回”，支持在前端修改部分 pool 属性，并查看每项写回结果和 SSH 执行日志。

## 当前能力

- 后端统一输出 `meta + data` 双层快照模型
- 轮询任务按 `disks`、`pools`、`datasets`、`properties` 分频执行
- SSH 采集失败时保留最近一次成功快照，并返回 `degraded` 或 `disconnected`
- 前端直接消费后端整理后的 `summary`、`disks`、`pools`、`datasets`
- Pools 详情抽屉支持编辑可写属性、确认保存、逐项结果回显与 SSH 日志查看
- 属性保存后后端会强制刷新一次状态，尽快把最新数据推回前端

## 目录

- `backend/`: FastAPI 后端、SSH 客户端、轮询与写回服务
- `frontend/`: Vue 3 + Vite 前端
- `Documents/`: 项目说明、阶段目标、协作约定

## 数据流

1. 后端 `StatePoller` 按计划执行 SSH 查询。
2. `parser` 将命令输出解析为结构化数据。
3. `poller` 基于解析结果生成 `summary`、`disks`、`pools`、`datasets`。
4. 快照写入内存中的 `state_store`，并通过 REST / WebSocket 对外提供。
5. 前端根据 `snapshot.meta` 展示连接与新鲜度，根据 `snapshot.data.*` 渲染页面。
6. 当用户保存 pool 属性时，后端执行 `zpool set`，返回每项结果，并强制刷新最新状态。

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

后端配置见 `backend/config.example.json`。当前阶段最关键的配置项包括：

- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`
- SSH 连接参数与命令超时
