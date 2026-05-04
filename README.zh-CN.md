# ZFS Manager

> [English Version](./README.md)

一个通过 SSH 管理远程 ZFS 主机的 Web 控制台。ZFS Manager 将常见的池、数据集和磁盘操作收敛到一个直观易用的界面中，日常任务无需切换到命令行。

## 功能特点

### 存储池管理
- 实时展示存储池使用率、健康状态和容量指标
- 可视化拓扑浏览，设备状态一目了然
- 创建、编辑属性、添加/移除设备、销毁存储池
- 创建存储池时同时配置根数据集属性

### 数据集与 Zvol 管理
- 层次化树形视图，支持展开/折叠
- 创建、修改、销毁数据集和 zvol
- 分组展示属性，支持 inline 编辑
- 可选的快照显示开关

### 磁盘监控
- 磁盘清单，含型号、类型和健康状态
- 分区和文件系统信息
- 存储池归属关联

### 实时更新
- WebSocket 驱动的实时状态同步
- 顶栏强制刷新
- 写操作后自动刷新

### 多语言支持
- 内置英文和简体中文
- 浏览器语言自动检测
- 语言偏好持久化

### 安全
- 可选的网页密码登录保护
- 基于 Cookie 的会话管理

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3, Vite, vue-router, Pinia, vue-i18n |
| 后端 | FastAPI, Pydantic, 异步 SSH |
| 传输 | REST (写操作), WebSocket (实时更新) |
| 通信 | SSH 连接远程 ZFS 主机 |

## 快速开始

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

## 文档

- [后端详情](./backend/README.md)
- [前端详情](./frontend/README.md)
- [项目文档](./Documents/README.md)
