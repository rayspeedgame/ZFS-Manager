# components/app

这一层是应用骨架组件。

## 文件说明

- `AppSidebar.js`: 左侧导航
- `AppTopbar.js`: 顶栏状态与全局操作
- `StatusBadge.js`: 小型状态徽标

## 当前重点

- `AppTopbar.js` 展示 WebSocket、SSH source、last success、data age 等状态
- 顶栏中的 `Force Refresh` 会调用后端全量刷新接口，而不是只读缓存
