# components/common

这里放通用基础组件。

## 文件说明

- `DetailDrawer.js`: 详情抽屉
- `ConfirmDialog.js`: 确认弹窗
- `EmptyState.js`: 空状态提示
- `JsonDebugPanel.js`: 调试用 JSON 展示

## 当前使用方式

- Pools 和 Datasets 详情使用 `DetailDrawer`
- 高风险保存/创建/删除流程使用 `ConfirmDialog`
- 页面数据为空或尚未准备好时优先通过 `EmptyState` 提示
