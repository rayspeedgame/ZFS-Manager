# components

> [English Version](./README.md)

可复用 Vue 组件放在这里。

## Structure

- `app/`: 应用壳组件，如导航和顶部状态 UI
- `common/`: 各工作流共享的视图无关基础组件
- `datasets/`: 数据集专用抽屉、表格、对话框和配置
- `pools/`: 池专用抽屉、拓扑 UI、对话框和配置

## 层级

- `common/` 应保持不含池或数据集特定字段名
- `datasets/` 和 `pools/` 可以依赖 `common/`，但应将后端调用保留在路由视图中
- 路由视图应组装这些组件并拥有页面级状态
