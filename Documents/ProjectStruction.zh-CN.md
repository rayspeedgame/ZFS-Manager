# Project Structure

> [English Version](./ProjectStruction.md)

## 后端

- `app/api`
  - REST 与 WebSocket 端点
- `app/core`
  - 共享的后端配置和应用接线
- `app/schemas`
  - 请求与响应模型
- `app/services`
  - ZFS 编排和刷新服务
- `app/ssh`
  - SSH 命令执行和解析器辅助函数

## 前端

- `components/app`
  - 应用壳组件，包括侧边栏、顶栏、刷新操作和语言切换器
- `components/common`
  - 共享的 UI 基础组件，用于抽屉、对话框、属性列表、命令结果和日志
- `components/pools`
  - 仅池的工作流组件和配置
- `components/datasets`
  - 仅数据集的工作流组件和配置
- `i18n`
  - 语言环境引导、浏览器语言检测、本地存储持久化和翻译消息包
- `router`
  - 路由定义和路由引导；路由元数据现在使用翻译键
- `stores`
  - Pinia store，拥有快照生命周期和 WebSocket 状态
- `services`
  - REST 写请求
- `store`
  - 仍然暴露 `useAppState()` 的兼容适配器
- `views`
  - 路由页面容器，组装较小的工作流组件

## 数据流

1. 后端轮询或刷新 ZFS 状态并将其规范化为快照。
2. 前端 store 通过 WebSocket 或按需刷新接收该快照。
3. 路由视图从快照中派生页面特定状态。
4. 子组件渲染 UI 并向上发送事件。
5. 路由视图调用 REST 服务层进行写操作，然后再次刷新状态。

## 前端重构成果

- 大型池和数据集页面被拆分为更小的工作流组件。
- 属性密集型 UI 现在共享 `PropertySection.vue` 和 `PropertyFieldList.vue`。
- 确认结果和 SSH 日志现在共享专用通用组件。
- 脏草稿保护防止实时快照更新覆盖用户当前输入。
- 语言切换由中心处理，应立即更新外壳导航和页面级工作流副本。
