# components/app

Application shell components.

## Files

- `AppSidebar.vue`: primary navigation
- `AppTopbar.vue`: top status area and global refresh action
- `StatusBadge.vue`: compact status pill

## Notes

- `AppTopbar.vue` shows WebSocket state, backend source state, last success time, and data age.
- The topbar `Refresh` action triggers the backend full refresh path rather than only reading cached state.
