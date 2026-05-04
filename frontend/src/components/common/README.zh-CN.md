# components/common

> [English Version](./README.md)

各视图共享的基础组件。

## Files

- `DetailDrawer.vue`: 侧滑详情面板
- `ConfirmDialog.vue`: 确认和结果对话框外壳
- `EmptyState.vue`: 空数据占位符
- `JsonDebugPanel.vue`: 仅开发使用的原始快照面板
- `PropertySection.vue`: 详情和表单区域的标签包装器
- `PropertyFieldList.vue`: 只读和可编辑字段列表的共享属性渲染器
- `CommandResultList.vue`: 紧凑的成功/失败结果行
- `CommandLogPanel.vue`: SSH 命令日志展示
- `property-options.js`: 池和数据集配置文件重用的共享选项列表

## Usage

- 池和数据集详情工作流使用 `DetailDrawer`
- 高风险保存/创建/删除流程使用 `ConfirmDialog`
- 空或尚未就绪的页面应优先使用 `EmptyState`
- 属性密集型抽屉在添加一次性标记之前应优先使用 `PropertySection` 和 `PropertyFieldList`
