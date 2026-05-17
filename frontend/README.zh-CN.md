# Frontend

> [English Version](./README.md)

前端使用 Vue 3、Vite、`vue-router`、Pinia 和 `vue-i18n`。它负责消费后端快照、渲染存储管理界面、展示任务历史，并把高风险写操作包装成清晰可确认的流程。

## 主要视图

- `Dashboard`
  - 实时摘要卡片和健康概览
- `Disks`
  - 磁盘清单、分区、文件系统标签和 pool 归属
- `Pools`
  - pool 概览、拓扑浏览、属性编辑、创建、移除、销毁和 `scrub`
- `Datasets`
  - dataset / zvol 树、snapshot 切换、属性编辑、创建和销毁
- `Tasks`
  - 最近写操作、任务状态、进度和命令日志
- `Settings`
  - 后端 SSH、轮询和网页登录设置

## 当前架构

- `src/App.vue`
  - 应用壳，根据登录状态显示登录页或主界面
- `src/components/app`
  - 侧边栏、顶部状态栏、登录门禁
- `src/components/common`
  - 通用抽屉、对话框、属性编辑和命令结果组件
- `src/components/pools`
  - pool 专用列表、拓扑抽屉、详情抽屉和创建流程组件
- `src/components/pools/PoolDetailDrawer.vue`
  - 包含 `scrub` 状态展示以及开始/停止按钮
- `src/views/PoolsView.vue`
  - 负责 pool 相关主工作流，并接入 `scrub` 请求
- `src/stores/tasks.js`
  - 任务列表缓存、单任务详情和周期刷新
- `src/services/api.js`
  - REST 写请求、任务接口、设置接口、认证接口和 `scrub` 接口
- `src/store/state.js`
  - 兼容 `useAppState()` 形状的适配层

## 国际化说明

- 当前支持 `en-US` 和 `zh-CN`
- 首次加载按浏览器语言选择中英文
- 用户语言选择会写入 `localStorage`
- 文案资源已经按语言和模块拆分
- 新增可见文本优先通过 `useI18n()` 获取

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
