# Project Directory Structure

> [English Version](./ProjectDirectoryStructure.md)

```text
ZFS-Manager/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- ssh/
|   |-- config/
|   |   |-- config.example.json
|   |   `-- config.json
|   |-- scripts/
|   |-- tests/
|   |   `-- fixtures/
|   |-- README.md
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- components/
|   |   |   |-- app/
|   |   |   |-- common/
|   |   |   |-- datasets/
|   |   |   `-- pools/
|   |   |-- i18n/
|   |   |   `-- messages/
|   |   |       |-- en-US/
|   |   |       `-- zh-CN/
|   |   |-- lib/
|   |   |-- router/
|   |   |-- services/
|   |   |-- store/
|   |   |-- stores/
|   |   `-- views/
|   |-- README.md
|   |-- index.html
|   |-- package.json
|   `-- vite.config.js
|-- Documents/
|   |-- README.md
|   |-- agent.md
|   |-- target.md
|   |-- ProjectStruction.md
|   `-- ProjectDirectoryStructure.md
`-- README.md
```

## 前端说明

- `frontend/src/views/SettingsView.vue`
  - 后端设置页，负责加载、编辑、保存、重载和 SSH 测试
- `frontend/src/components/app/AppLoginGate.vue`
  - 网页密码登录界面
- `frontend/src/App.vue`
  - 根据登录状态决定显示登录页还是主应用壳
- `frontend/src/i18n/messages/`
  - 翻译资源已经按语言和模块拆分
  - 每种语言下包含 `app`、`routes`、`common`、`dashboard`、`disks`、`pools`、`datasets`、`settings`、`properties`、`login`

## 后端说明

- `backend/config/`
  - 当前正式配置目录
- `backend/app/core/config.py`
  - 配置加载、保存、路径解析和环境变量覆盖
- `backend/app/core/auth.py`
  - 轻量登录态处理
- `backend/app/api/rest.py`
  - 状态接口、设置接口、认证接口和各类 ZFS 写接口
- `backend/app/main.py`
  - 应用启动、CORS 与认证中间件

## 相关热点

- 配置与认证
  - `backend/app/core/config.py`
  - `backend/app/core/auth.py`
  - `backend/app/api/rest.py`
  - `backend/app/main.py`
- 前端状态与登录门禁
  - `frontend/src/stores/app.js`
  - `frontend/src/store/state.js`
  - `frontend/src/App.vue`
  - `frontend/src/components/app/AppLoginGate.vue`
- 前端国际化
  - `frontend/src/i18n/index.js`
  - `frontend/src/i18n/messages.js`
  - `frontend/src/i18n/messages/en-US/`
  - `frontend/src/i18n/messages/zh-CN/`
