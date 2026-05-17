# Frontend

> [English Version](./README.md)

前端使用 Vue 3、Vite、`vue-router`、Pinia 和 `vue-i18n`。它负责消费后端快照、渲染存储管理界面、展示任务记录与计划任务，并把高风险写操作包装成清晰可确认的流程。

## 主要视图

- `Dashboard`
  - 实时摘要卡片和健康概览
- `Disks`
  - 磁盘清单、分区、文件系统标签和 pool 归属
- `Pools`
  - pool 概览、拓扑浏览、属性编辑、创建、移除、销毁和 `scrub`
- `Datasets`
  - dataset / zvol 树、snapshot 切换、属性编辑、创建和销毁
- `Schedules`
  - 定时 `scrub` 管理，以及定时快照占位区
- `Tasks`
  - 任务记录、实时状态、进度、筛选、分页和命令日志
- `Settings`
  - 后端 SSH、轮询和网页登录设置

## 当前架构

- `src/App.vue`
  - 应用壳，根据认证状态决定显示登录门禁还是主界面
- `src/components/app`
  - 侧边栏、顶部状态栏、登录门禁等壳层组件
- `src/components/common`
  - 通用抽屉、对话框、属性编辑器和命令结果组件
- `src/components/pools`
  - pool 专用列表、抽屉、拓扑和创建流程组件
- `src/components/datasets`
  - dataset 专用树、抽屉和创建流程组件
- `src/i18n/index.js`
  - 语言初始化、浏览器语言检测和本地持久化
- `src/i18n/messages/en-US/` 与 `src/i18n/messages/zh-CN/`
  - 按模块拆分的翻译资源
- `src/router/routes.js`
  - 仪表盘、磁盘、存储池、数据集、计划任务、任务和设置的路由元数据
- `src/stores/app.js`
  - WebSocket 生命周期、快照缓存、认证状态和刷新动作
- `src/stores/tasks.js`
  - 任务记录列表、选中详情、分页、状态筛选和周期刷新逻辑
- `src/services/api.js`
  - REST 写接口、任务接口、计划任务接口、设置接口和认证接口
- `src/store/state.js`
  - 兼容旧 `useAppState()` 形状的适配层

## 国际化说明

- 当前支持 `en-US` 和 `zh-CN`
- 首次加载按浏览器语言选择语种
- 用户语言选择会写入 `localStorage`
- 文案资源已按语言和模块拆分
- 新增用户可见文本优先通过 `useI18n()` 获取，而不是直接硬编码

## 认证说明

- 网页密码登录默认关闭
- 开启后，前端会先请求 `/api/auth/status`
- 未登录时显示 `AppLoginGate.vue`
- 登录成功后再建立 WebSocket 连接并进入主界面

## 开发

```bash
npm install
npm run dev
npm run build
```
