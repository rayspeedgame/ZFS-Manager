# components/common

> [中文版本](./README.zh-CN.md)

Shared base components used across views.

## Files

- `DetailDrawer.vue`: slide-over detail panel
- `ConfirmDialog.vue`: confirmation and result dialog shell
- `EmptyState.vue`: empty-data placeholder
- `JsonDebugPanel.vue`: development-only raw snapshot panel
- `PropertySection.vue`: labeled wrapper for detail and form sections
- `PropertyFieldList.vue`: shared property renderer for readonly and editable field lists
- `CommandResultList.vue`: compact success/failure result rows
- `CommandLogPanel.vue`: SSH command log presentation
- `HelpTooltip.vue`: `?` help icon next to property labels, shows multi-line description on hover
- `property-options.js`: shared option lists reused by pool and dataset config files

## Usage

- Pools and Datasets detail workflows use `DetailDrawer`.
- High-risk save/create/delete flows use `ConfirmDialog`.
- Empty or not-yet-ready pages should prefer `EmptyState`.
- Property-heavy drawers should prefer `PropertySection` and `PropertyFieldList` before adding one-off markup.
