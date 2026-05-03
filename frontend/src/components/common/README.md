# components/common

Shared base components used across views.

## Files

- `DetailDrawer.vue`: slide-over detail panel
- `ConfirmDialog.vue`: confirmation and result dialog shell
- `EmptyState.vue`: empty-data placeholder
- `JsonDebugPanel.vue`: development-only raw snapshot panel

## Usage

- Pools and Datasets detail workflows use `DetailDrawer`.
- High-risk save/create/delete flows use `ConfirmDialog`.
- Empty or not-yet-ready pages should prefer `EmptyState`.
