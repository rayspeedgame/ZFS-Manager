# src

> [English Version](./README.md)

`src/` 保存 Vue 前端源码。

## 结构

- `App.vue`：根应用壳与登录门禁切换
- `main.js`：应用启动入口
- `i18n/`：语言初始化与翻译资源
- `styles.css`：全局共享样式
- `components/`：可复用 UI 组件
- `lib/`：格式化辅助函数
- `router/`：路由创建与路由元数据
- `services/`：REST API 调用
- `store/`：兼容适配层
- `stores/`：Pinia store
- `views/`：路由级页面容器

## 当前笔记

- `PoolsView.vue` 和 `DatasetsView.vue` 继续作为页面容器，负责 API 调用、实时快照重绑定和草稿保护
- `TasksView.vue` 现在负责任务记录浏览、状态筛选、分页和详情加载
- `SchedulesView.vue` 负责定时 `scrub` 定义以及未来定时快照占位区
- `DisksView.vue` 在磁盘表中内置 SMART 健康列，并通过 `ConfirmDialog` 展示完整属性弹窗
- `SettingsView.vue` 负责设置读取、保存、SSH 测试、登录配置编辑和 SMART 轮询间隔
- `i18n/messages.js` 现在只是聚合入口，真正的翻译资源位于 `i18n/messages/<locale>/<module>.js`
- 路由定义仍暴露翻译 key，这样切换语言时侧边栏和标题会立即更新
