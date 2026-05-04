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
- 暴露 REST 接口：
  - 状态读取与强制刷新
  - 设置读取、保存与 SSH 测试
  - 登录状态、登录、退出
  - pool 和 dataset 写操作
- 通过 WebSocket 推送最新快照

## 目录说明

- `app/api/`: REST 与 WebSocket 入口
- `app/core/`: 配置、认证、共享状态等基础设施
- `app/schemas/`: Pydantic 请求、响应与快照模型
- `app/services/`: 轮询、状态聚合、写操作执行
- `app/ssh/`: SSH 客户端、命令定义、解析器
- `config/`: 当前使用的配置目录
- `tests/fixtures/`: fixture 模式输入样例

## 当前实现重点

- `StatePoller` 按 `pools / datasets / disks / properties` 分频刷新
- 写操作完成后统一调用 `poller.refresh_once(force_all=True)`
- 设置保存后会热重载 runtime，而不是要求手动重启后端
- 认证是轻量 cookie 登录，默认关闭，可由设置页启用

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```
