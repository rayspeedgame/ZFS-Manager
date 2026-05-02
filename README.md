# ZFS Manager

ZFS Manager 是一个通过 SSH 管理远端 ZFS 主机的 Web 控制台。项目由 FastAPI 后端、Vue 3 前端和一组轮询/解析服务组成，目标是把常见的 ZFS 状态查看与 pool 操作放到统一界面里完成。

## 当前功能

- 实时展示 `disks`、`pools`、`datasets` 和汇总统计
- 通过 WebSocket 持续推送最新快照，写操作后通过 REST 主动刷新
- 查看 pool 拓扑，并显示整盘路径、`/dev/disk/by-id`、pool 内状态和 R/W/C
- 修改 pool 可编辑属性，并回显每条 SSH 执行结果
- 为现有 pool 添加附加设备
  - `log / ZIL`
  - `cache / L2ARC`
  - `special`
  - `dedup`
  - `spare`
- 创建新 pool
  - 基础属性设置
  - `data vdev` 分步构建
  - 附加设备分步构建
  - 最终以一条原子化 `zpool create` 命令提交
- 删除 pool
- 移除可删除的拓扑目标
  - 有阵列时优先移除阵列
  - 无阵列时才暴露单盘移除
- 对已 `destroy`、但仍保留 `zfs_member` 标签的磁盘做“inactive”识别，既保留提示，也允许再次用于建池或附加设备

## 目录

- [backend/README.md](./backend/README.md): 后端服务、接口、SSH 写入链路
- [frontend/README.md](./frontend/README.md): 前端视图、抽屉、确认弹窗与状态同步
- [Documents/README.md](./Documents/README.md): 补充说明、结构文档与目标说明

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

## 配置说明

后端通过 `backend/config.json` 读取轮询和 SSH 配置，常见项包括：

- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`
- SSH 连接地址、账号、密钥或密码

建议先参考 `backend/config.example.json`。
