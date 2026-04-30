zfs-manager/
├── backend/                  # === 第二层到第四层：Python 后端服务 ===
│   ├── app/
│   │   ├── api/              # 接口层 (Routers)
│   │   │   ├── rest.py       # 处理前端的主动请求 (如创建 Dataset)
│   │   │   └── ws.py         # WebSocket 连接管理与状态推送
│   │   ├── core/             # 核心机制
│   │   │   ├── config.py     # 读取环境变量或配置文件 (如 SSH 密钥路径、目标 IP)
│   │   │   └── state.py      # 【核心】全局内存状态机单例 (存放最新 Pydantic 数据)
│   │   ├── db/               # 持久化层 (SQLite)
│   │   │   ├── engine.py     # 初始化 SQLModel 和 SQLite 引擎
│   │   │   └── models.py     # SQLModel 数据表结构 (持久化数据)
│   │   ├── schemas/          # 数据校验层 (Pydantic Models)
│   │   │   └── zfs_state.py  # 内存中的 ZFS 和硬盘状态数据结构
│   │   ├── services/         # 业务逻辑与后台任务
│   │   │   ├── poller.py     # 【核心】后台异步轮询引擎 (控制频率、打点采样)
│   │   │   └── zfs_mgr.py    # ZFS 配置修改的业务逻辑封装
│   │   ├── ssh/              # 调度与解析层
│   │   │   ├── client.py     # 维护 asyncssh 长连接池
│   │   │   ├── commands.py   # 集中管理所有发往宿主机的 Linux 命令字符串
│   │   │   └── parser.py     # 文本/JSON 解析器 (将系统输出转为字典)
│   │   └── main.py           # FastAPI 入口文件，组装所有模块
│   ├── tests/                # 后端测试目录 (极其重要)
│   ├── pyproject.toml        # Python 依赖管理 (建议使用 poetry 或 uv)
│   └── requirements.txt      
│
├── frontend/                 # === 第一层：Vue 3 前端表现层 ===
│   ├── src/
│   │   ├── api/              # 封装 Axios 请求 (对应后端的 rest.py)
│   │   ├── assets/           # 静态资源 (图片、全局 CSS)
│   │   ├── components/       # 可复用组件 (如：硬盘卡片、ZFS容量进度条)
│   │   ├── router/           # Vue Router 前端路由控制
│   │   ├── stores/           # Pinia 状态管理 (接收 WebSocket 数据并分发给组件)
│   │   ├── views/            # 独立页面 (Dashboard.vue, Storage.vue 等)
│   │   └── App.vue           # 前端根组件
│   ├── index.html            
│   ├── package.json          # Node.js 依赖管理
│   ├── tailwind.config.js    # Tailwind CSS 配置文件
│   └── vite.config.ts        # Vite 构建配置 (配置代理解决跨域)
│
├── host_scripts/             # === 第五层：部署在 PVE 宿主机上的脚本 ===
│   └── zfs-wrapper.sh        # SSH ForceCommand 拦截与安全校验脚本
│
├── .gitignore
└── docker-compose.yml        # 用于一键部署整个后端与数据库