# ZFS Manager

ZFS Manager 是一个通过 SSH 管理远程 ZFS 主机的 Web 控制台。项目由 FastAPI 后端、Vue 3 前端，以及一组状态轮询与写操作服务组成，目标是把常见的池、数据集、磁盘查看与管理收敛到同一个界面里。

## 当前能力

- 实时展示 `disks`、`pools`、`datasets` 和总览摘要
- 通过 WebSocket 推送最新快照，写操作后通过 REST 主动触发强制刷新
- 查看 pool 拓扑、磁盘 `by-id`、健康状态和可移除目标
- 修改 pool 属性，新增 topology 设备，创建、删除、移除 pool
- 在创建 pool 时同时配置 root dataset 属性
- 管理 dataset / zvol
  - 树形 inventory
  - 详情抽屉
  - 固定属性与可编辑属性分组
  - 创建、修改、删除
  - snapshot 可选显示
- 在网页中编辑后端设置
  - SSH 连接参数
  - 轮询频率
  - 是否允许 SSH 失败后回退到 fixture
  - SSH 测试连接
- 可选启用网页登录密码
  - 默认关闭
  - 启用后先经过登录页再进入主界面
- 顶栏支持全量 `force refresh`
- 内置中英文切换，并持久化用户语言选择

## 目录

- [backend/README.md](./backend/README.md): 后端服务、接口、轮询与 SSH 写入链路
- [frontend/README.md](./frontend/README.md): 前端视图、组件、登录门禁、设置页与 i18n
- [Documents/README.md](./Documents/README.md): 项目说明、结构文档与维护说明

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

后端优先从 `backend/config/config.json` 读取配置，示例文件位于 `backend/config/config.example.json`。

主要配置块：

- `poller`
  - `mode`
  - `fallback_to_fixture`
  - `interval_seconds`
  - `tick_seconds`
  - `pools_interval_seconds`
  - `datasets_interval_seconds`
  - `disks_interval_seconds`
  - `properties_interval_seconds`
- `ssh`
  - 主机、端口、用户名、密码、密钥、known_hosts、超时和 keepalive
- `auth`
  - `enabled`
  - `password`

也支持环境变量覆盖。设置页保存后，后端会写回配置文件并热重载运行时服务。
