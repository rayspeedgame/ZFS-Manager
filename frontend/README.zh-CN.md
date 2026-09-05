# Frontend

> [English Version](./README.md)

前端使用 Vue 3、路由页面、共享弹窗和 i18n 来承载存储管理界面、任务记录和周期任务工作流。

## 当前职责

- 渲染 Dashboard、磁盘、pool、dataset、snapshot、schedule、task 和设置八个路由页面
- 通过 WebSocket 接收统一状态快照，并通过 REST 执行查询与写操作
- 支持磁盘自定义标签、SMART 详情、设置编辑、SSH 测试和可选登录门禁
- 让周期任务交互风格与全站保持一致
- 使用共享确认弹窗承载危险操作
- 所有用户可见文案统一走 i18n

## 当前重点页面

- `SnapshotsView`：集中快照管理
- `SchedulesView`：定时 `scrub` 与定时 `snapshot`
- `TasksView`：任务记录与状态
- `DatasetsView`：手动快照快速发起
- `SettingsView`：轮询配置，含独立的活跃和空闲间隔控制

## 当前计划任务界面特点

- `scrub` 和 `snapshot` 共用同一个计划任务页面
- 快照计划支持：
  - 分钟级
  - 小时级
  - 天级
  - 周级
  - 月级
- 删除计划任务已经改为统一的站内确认弹窗，而不是浏览器原生弹窗
- `scrub` 计划当前只支持每周频率
- 页面支持计划创建、启停和删除；后端虽支持局部更新，当前尚无完整编辑表单

## 本地开发配置

- 开发模式默认连接当前主机的 `8000` 端口，生产模式默认同源
- `VITE_BACKEND_ORIGIN` 可指定完整后端源地址，`VITE_BACKEND_PORT` 可只覆盖端口
- `VITE_SHOW_JSON_DEBUG=true` 可显示 Dashboard 的 JSON 调试面板
