# ZFS Manager

ZFS Manager 是一个通过 SSH 管理远程 ZFS 主机的 Web 控制台。项目由 FastAPI 后端、Vue 3 前端和一组状态轮询/解析服务组成，目标是把常见的池、数据集、磁盘查看与写操作放到统一界面里完成。

## 当前能力

- 实时展示 `disks`、`pools`、`datasets` 和汇总统计
- 通过 WebSocket 推送最新快照，写操作后通过 REST 主动强制刷新
- 查看 pool 拓扑、磁盘 by-id、R/W/C 校验状态和可移除目标
- 修改 pool 属性，新增 topology 设备，创建/删除 pool
- 在创建 pool 时同时设置 root dataset 属性
- 管理 dataset / zvol
  - 树形 inventory
  - 详情抽屉
  - 固定属性与可修改属性分组
  - 创建 / 修改 / 删除
  - snapshot 可选显示
- 顶栏支持全量 `force refresh`，会触发后端重新采集全部数据

## 目录

- [backend/README.md](./backend/README.md): 后端服务、接口、轮询与 SSH 写入链路
- [frontend/README.md](./frontend/README.md): 前端视图、抽屉、确认弹窗与状态同步
- [Documents/README.md](./Documents/README.md): 项目说明、结构文档与目标文档

## 运行

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

## 配置

后端通过 `backend/config.json` 读取轮询与 SSH 配置，常见项包括：

- `poller.mode`
- `poller.fallback_to_fixture`
- `tick_seconds`
- `pools_interval_seconds`
- `datasets_interval_seconds`
- `disks_interval_seconds`
- `properties_interval_seconds`
- SSH 主机、端口、用户名、密码/密钥

建议先参考 `backend/config.example.json`。
