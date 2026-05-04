# components/datasets

> [English Version](./README.md)

数据集专用工作流组件。

## Files

- `DatasetTreeTable.vue`: 数据集和快照树展示
- `DatasetDetailDrawer.vue`: 只读详情加上可编辑的数据集属性
- `CreateDatasetDrawer.vue`: 数据集和 zvol 创建表单
- `DatasetActionDialogs.vue`: 数据集写操作的确认和结果对话框
- `dataset-form-config.js`: 可编辑字段、创建表单组和属性输入配置

## Notes

- 这些组件渲染数据集工作流，但不直接调用后端
- `DatasetsView.vue` 拥有选择状态、API 调用和实时快照重新绑定
