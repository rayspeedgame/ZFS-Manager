# components/app

> [中文版本](./README.zh-CN.md)

Application shell components.

## Files

- `AppSidebar.vue`: Main navigation
- `AppTopbar.vue`: Top status area, language switch, refresh, and logout
- `AppLoginGate.vue`: Web password login interface
- `StatusBadge.vue`: Compact status badge

## Notes

- `AppTopbar.vue` displays WebSocket status, backend data source status, last success time, and data freshness
- Topbar's `Refresh` triggers a full backend refresh, not just reading cached data
- `AppLoginGate.vue` is only shown when web login is enabled and currently unauthenticated
