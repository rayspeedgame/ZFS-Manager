# Backend

后端负责三件事：采集远程主机状态、把原始命令输出整理成统一快照、执行 ZFS/ZPool 写操作并在完成后强制刷新状态。

## 主要职责

- 通过 SSH 执行只读命令，采集：
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status/list/get`
  - `zfs list/get`
- 把原始输出解析为统一的 `meta + data` 快照
- 暴露 REST 写接口：
  - pool 属性修改
  - pool topology 变更
  - pool 创建 / 删除 / remove
  - dataset 属性修改
  - dataset / zvol 创建 / 删除
- 通过 WebSocket 推送最新快照

## 目录说明

- `app/api/`: REST 与 WebSocket 入口
- `app/core/`: 配置加载、共享状态存储
- `app/schemas/`: Pydantic 请求/响应与快照模型
- `app/services/`: 轮询、状态聚合、写操作执行器
- `app/ssh/`: SSH 客户端、命令定义、解析器
- `tests/fixtures/`: fixture 模式输入样例

## 当前实现重点

- `StatePoller` 按 `pools / datasets / disks / properties` 分频刷新
- `poller.refresh_once(force_all=True)` 用于写操作后的全量强刷
- dataset 列表顺序与层级字段现在由后端统一整理，前端只负责展示和折叠
- 所有高风险写操作都返回命令、退出码、stdout、stderr，便于排查

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
