# src

`src/` 是前端主代码目录。

## 文件与目录

- `App.js`: 应用框架
- `main.js`: 入口
- `styles.css`: 全局样式
- `components/`: 复用组件
- `lib/`: 格式化工具
- `router/`: 路由定义
- `store/`: 前端状态与 WebSocket 管理
- `views/`: 页面级视图

## 当前实现重点

前端当前主要承担展示职责，尽量不再自行推断池关系、拼接分区归属或计算页面主数据。
