# Frontend

前端基于 Vue 3 + Vite，核心职责是消费后端快照、组织交互流程，并把 pool 写操作做成可确认、可回显、可追踪的 UI。

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
  - 拓扑编辑抽屉
  - 新建 pool 向导
  - 删除 pool / 移除设备确认流
- `Datasets`
  - dataset 快照与属性展示

## 与 pool 新功能相关的实现点

- `src/views/PoolsView.js`
  - pool 总览与展开区
  - pool 属性修改
  - pool 拓扑设备添加
  - 新建 pool 分步向导
  - 删除 pool
  - 移除拓扑目标
- `src/store/state.js`
  - REST 写接口调用
  - `refreshStateOnce()` 主动同步
- `src/styles.css`
  - 拓扑卡片
  - 危险按钮
  - 等待态 spinner

## 交互约定

- 所有 pool 写操作都先弹出确认框
- 提交后展示 loading 状态
- 完成后展示：
  - 成功/失败摘要
  - SSH 命令日志
  - 刷新错误（如果有）
- 前端在写操作完成后会再请求一次 `/api/state`，减少 WebSocket 延迟带来的旧状态残留

## 启动

```bash
npm install
npm run dev
```
