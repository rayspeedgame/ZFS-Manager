# src

`src/` 保存 Vue 前端源码。

## Structure

- `App.vue`: 根应用壳与登录门禁切换
- `main.js`: 应用启动入口
- `i18n/`: 语言初始化与翻译资源
- `styles.css`: 全局共享样式
- `components/`: 可复用 UI 组件
- `lib/`: 格式化辅助函数
- `router/`: 路由创建与元数据
- `services/`: REST API 调用
- `store/`: 兼容适配层
- `stores/`: Pinia store
- `views/`: 路由级页面容器

## Current Notes

- `PoolsView.vue` 和 `DatasetsView.vue` 继续作为页面容器，负责 API 调用、实时快照重绑定和草稿保护
- `SettingsView.vue` 负责设置读取、保存、SSH 测试和登录配置编辑
- `App.vue` 负责根据认证状态显示登录界面或主应用
- `i18n/messages.js` 现在只是聚合入口，真正的翻译资源位于 `i18n/messages/<locale>/<module>.js`
- 路由定义继续暴露翻译 key，这样切换语言时侧边栏和标题会立即更新
