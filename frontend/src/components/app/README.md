# components/app

这一层是应用骨架组件。

## 文件说明

- `AppSidebar.js`: 左侧导航
- `AppTopbar.js`: 顶栏状态和全局信息
- `StatusBadge.js`: 小型状态徽标

## 当前重点

`AppTopbar.js` 现在会展示两种状态：

- WebSocket 状态
- 后端 `meta.app_status` / `meta.source_status`

其中来源状态会使用绿色、橙色、红色做明确反馈。
