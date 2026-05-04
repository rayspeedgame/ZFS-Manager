# components/datasets

> [中文版本](./README.zh-CN.md)

Dataset-specific workflow components.

## Files

- `DatasetTreeTable.vue`: dataset and snapshot tree presentation
- `DatasetDetailDrawer.vue`: readonly details plus editable dataset properties
- `CreateDatasetDrawer.vue`: dataset and zvol create form
- `DatasetActionDialogs.vue`: confirmation and result dialogs for dataset writes
- `dataset-form-config.js`: editable fields, create form groups, and property input config

## Notes

- These components render dataset workflows but do not call the backend directly.
- `DatasetsView.vue` owns selection state, API calls, and live snapshot rebinding.
