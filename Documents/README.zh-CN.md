# Documents

> [English Version](./README.md)

这个目录保存面向维护者和后续开发者的项目说明文档。

## 文件

- `agent.md`: 新协作者或编码代理的快速上手说明
- `target.md`: 当前产品目标、已完成功能与后续方向
- `ProjectStruction.md`: 高层架构与职责分层
- `ProjectDirectoryStructure.md`: 当前目录结构与关键模块分布

## 当前关注点

- 后端配置文件已经统一收敛到 `backend/config/`
- 前端新增了设置页，可直接编辑 SSH、轮询和登录相关配置
- 后端提供了设置读取、保存、SSH 测试、登录状态、登录与退出接口
- 前端支持可选密码登录门禁，默认关闭
- 前端国际化已拆成按语言加按模块的结构，便于后续继续扩展中文和新增页面文案
