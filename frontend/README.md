# Frontend

前端使用 Vue 3 和 Vite，负责展示后端输出的结构化快照，并提供 pool 属性编辑交互。

## 当前阶段特点

- 页面优先消费 `snapshot.data.*`
- 顶栏区分 WebSocket 状态和后端数据源状态
- Dashboard、Disks、Pools、Datasets 都使用后端整理后的数据
- Pools 详情页支持编辑、确认保存、结果回显和 SSH 日志查看

## 启动

```bash
npm install
npm run dev
```

## 页面方向

- Dashboard: 全局概览
- Disks: 磁盘与分区
- Pools: 池、拓扑、属性查看与编辑
- Datasets: 数据集与常用属性
