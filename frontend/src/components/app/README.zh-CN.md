# components/app

> [English Version](./README.md)

应用壳层组件。

## Files

- `AppSidebar.vue`: 主导航
- `AppTopbar.vue`: 顶部状态区、语言切换、刷新和退出登录
- `AppLoginGate.vue`: 网页密码登录界面
- `StatusBadge.vue`: 紧凑状态标记

## Notes

- `AppTopbar.vue` 展示 WebSocket 状态、后端数据源状态、上次成功时间和数据时效
- 顶栏的 `Refresh` 会触发后端全量刷新，而不是只读取缓存
- `AppLoginGate.vue` 只在开启网页登录且当前未认证时显示
