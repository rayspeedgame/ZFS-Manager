# Backend

后端负责三件事：采集远端状态、把原始输出解析成统一快照、执行 pool 相关写操作并刷新状态。

## 主要职责

- 通过 SSH 执行只读命令，采集：
  - `lsblk`
  - `blkid`
  - `zpool status/list/get`
  - `zfs list/get`
- 把原始输出解析为统一的 `meta + data` 快照
- 通过 REST 暴露写操作：
  - 修改 pool 属性
  - 添加 pool 拓扑设备
  - 创建 pool
  - 删除 pool
  - 移除拓扑目标
- 通过 WebSocket 推送最新快照

## 目录说明

- `app/api/`
  - REST 和 WebSocket 入口
- `app/core/`
  - 配置加载、内存状态存储
- `app/schemas/`
  - Pydantic 请求/响应模型
- `app/services/`
  - 轮询器、pool 创建器、属性更新器、拓扑更新器、删除器
- `app/ssh/`
  - SSH 客户端、命令定义、解析器
- `tests/fixtures/`
  - 本地 fixture 模式输入样例

## 与 pool 功能相关的关键文件

- `app/api/rest.py`
  - pool 相关 REST 接口
- `app/services/pool_creator.py`
  - 原子化 `zpool create` 生成与执行
- `app/services/topology_updater.py`
  - `zpool add` 写入链路
- `app/services/pool_destroyer.py`
  - `zpool destroy`
- `app/services/pool_remover.py`
  - `zpool remove`
- `app/services/poller.py`
  - pool 行数据聚合
  - 磁盘与 by-id 映射
  - 可用设备筛选
  - `removalTargets` 生成

## 状态刷新策略

所有 pool 写接口在命令执行后都会调用：

```python
await poller.refresh_once(force_all=True)
```

这样前端拿到的结果不是本地推测，而是刷新后的真实主机状态。

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
