# Frontend

> [English Version](./README.md)

前端使用 Vue 3 单文件组件，运行在 Vite、`vue-router`、Pinia 和 `vue-i18n` 之上。它负责消费后端快照、渲染存储管理界面，并把高风险写操作包装成清晰可确认的流程。

## 主要视图

- `Dashboard`
  - 实时摘要卡片和健康概览
- `Disks`
  - 磁盘清单、分区、文件系统标签和 pool 归属
- `Pools`
  - pool 概览、拓扑浏览、属性编辑、创建、移除和销毁
- `Datasets`
  - dataset / zvol 树、snapshot 切换、属性编辑、创建和销毁
- `Settings`
  - 后端 SSH、轮询与网页登录设置

## 当前架构

- `src/App.vue`
  - 应用壳，负责根据登录状态显示登录页或主界面
- `src/components/app`
  - 壳层组件，包括侧边栏、顶栏、登录门禁
- `src/components/common`
  - 通用抽屉、对话框、属性编辑和命令结果组件
- `src/components/pools`
  - pool 专用列表、抽屉、拓扑和创建流程组件
- `src/components/datasets`
  - dataset 专用树、抽屉和创建流程组件
- `src/i18n/index.js`
  - 语言初始化、浏览器语言识别、本地持久化
- `src/i18n/messages.js`
  - 总翻译入口，聚合各语言资源
- `src/i18n/messages/en-US/` 与 `src/i18n/messages/zh-CN/`
  - 按模块拆分的翻译资源
- `src/router/routes.js`
  - 顶层路由元数据，使用翻译 key 而不是直接写文案
- `src/stores/app.js`
  - WebSocket 生命周期、快照缓存、认证状态、刷新动作
- `src/services/api.js`
  - REST 写请求、设置接口和认证接口
- `src/store/state.js`
  - 兼容旧 `useAppState()` 形状的适配层

## 国际化说明

- 当前支持 `en-US` 和 `zh-CN`
- 首次加载按浏览器语言选择中英文
- 用户语言选择会写入 `localStorage`
- 文案资源已经按语言加模块拆分，后续扩展新页面时优先往对应模块中追加
- 新的可见文案应优先走 `useI18n()`，避免直接硬编码

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
