# Frontend

前端使用 Vue 3 与 Vite，负责展示后端输出的结构化快照。

## 当前阶段特点

- 页面优先消费 `snapshot.data.*`
- 顶栏显式区分 WebSocket 连接状态和后端来源状态
- Dashboard、Disks、Pools、Datasets 都已切到后端整理后的数据层

## 启动

```bash
npm install
npm run dev
```

## 页面方向

- Dashboard: 全局摘要
- Disks: 磁盘与分区
- Pools: 池、拓扑与属性
- Datasets: 数据集与常用属性
