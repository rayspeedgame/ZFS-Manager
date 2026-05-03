# Frontend

前端基于 Vue 3 + Vite，核心职责是消费后端快照、组织交互流程，并把高风险写操作做成可确认、可回显、可追踪的 UI。

## 主要视图

- `Dashboard`
  - 汇总状态与关键指标
- `Disks`
  - 整盘、分区、文件系统、pool 归属
  - inactive `zfs_member` 识别
- `Pools`
  - pool 总览
  - 拓扑展开区
  - 属性编辑抽屉
  - topology 编辑抽屉
  - 新建 pool 向导
  - 删除 pool / 移除设备确认流
- `Datasets`
  - dataset / zvol inventory
  - 可选显示 snapshot
  - 管理抽屉
  - 创建 / 修改 / 删除

## 当前实现重点

- `src/views/PoolsView.js`
  - pool 属性、topology、新建、删除、remove
- `src/views/DatasetsView.js`
  - dataset 树形 inventory、snapshot 开关、属性分组、创建/删除流
- `src/store/state.js`
  - WebSocket 状态
  - REST 写接口
  - 普通刷新与全量强制刷新
- `src/styles.css`
  - 全局布局、状态面板、表格、抽屉、确认弹窗

## 交互约定

- 所有高风险写操作都先弹出确认框
- 提交后显示 loading 状态
- 完成后展示结果摘要、SSH 日志和刷新错误
- 前端在写操作完成后会再请求一次 `/api/state` 或 `/api/state/refresh`

## 启动

```bash
npm install
npm run dev
```
