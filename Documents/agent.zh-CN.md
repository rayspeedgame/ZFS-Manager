# Agent Guide

> [English Version](./agent.md)

本文档帮助新的贡献者理解数据从哪里来、写操作到哪里去，以及哪些区域最容易出问题。

## 技术栈

- 后端: FastAPI + Pydantic + 异步 SSH
- 前端: Vue 3 + Vite + `vue-router` + Pinia + `vue-i18n`
- 传输: REST 用于写操作，WebSocket 用于实时快照

## 核心概念

### 快照优先的 UI

- 前端应优先使用后端提供的 `snapshot.data.*`，而不是在本地重建 ZFS 状态。
- 数据集深度、父子关系、短名称和排序应尽可能使用后端准备的字段。

### 写操作流程契约

大多数池和数据集的变更遵循相同的生命周期：

1. 在前端验证用户输入。
2. 提交 REST 写请求。
3. 通过后端 SSH 服务执行命令。
4. 成功后立即触发刷新（部分成功也触发）。
5. 同时显示摘要和详细命令结果。

### 重构后的视图容器

- `frontend/src/views/PoolsView.vue`
  - 拥有所选池状态、对话框状态、实时快照重新绑定和脏草稿保护
- `frontend/src/views/DatasetsView.vue`
  - 拥有所选数据集状态、树形展开、创建/销毁流程和脏草稿保护
- `frontend/src/components/common/`
  - 托管共享属性编辑器、命令结果渲染和日志展示
- `frontend/src/components/pools/` 和 `frontend/src/components/datasets/`
  - 托管仅 UI 的工作流片段，向页面容器发送事件

### 语言系统

- `frontend/src/i18n/index.js` 从 `localStorage` 首先选择初始语言，然后是浏览器语言，最后是后备语言。
- `frontend/src/i18n/messages.js` 保存分组的翻译键，用于外壳、路由、通用 UI、仪表盘、池和数据集。
- 路由元数据应使用 `labelKey` 和 `descriptionKey`，以便导航和视图标题响应语言变化。
- 添加 UI 文本时，优先使用翻译键而非原始字符串，除非该值是应保持原样的领域原生标记。

## 关键维护入口点

- 读取路径
  - `backend/app/services/poller.py`
  - `backend/app/ssh/parser.py`
  - `frontend/src/stores/app.js`
- 写入路径
  - `backend/app/api/rest.py`
  - `backend/app/services/pool_creator.py`
  - `backend/app/services/topology_updater.py`
  - `backend/app/services/dataset_creator.py`
  - `backend/app/services/dataset_property_updater.py`
  - `backend/app/services/dataset_destroyer.py`
  - `frontend/src/services/api.js`

## 常见坑点

- 实时快照可能在用户编辑表单时到达，因此页面容器必须在重新绑定新快照数据之前保护脏草稿。
- 数据集名称可能包含 `/`，因此 REST 路由必须继续使用 `{dataset_name:path}`。
- "显示快照"保持可选，因为大型快照集会产生大量 UI 噪音。
- `frontend/src/store/state.js` 仍然是兼容层；新的状态工作应优先使用 `frontend/src/stores/app.js` 中的 Pinia store。
- 长生命周期数组中的语言敏感标签通常应包装在 `computed()` 中，以便切换语言时立即更新当前视图。
