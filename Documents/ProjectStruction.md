整个系统被划分为 **5个逻辑层**，它们职责分明，非常适合使用 AI 辅助工具（如 Cursor 等）进行模块化开发。

### 1. 前端表现层 (UI Layer)
**技术栈：** Vue 3 (Composition API) + Vite + Tailwind CSS + 组件库 (PrimeVue/Element Plus)
**核心功能：** 系统的“仪表盘”与“遥控器”，纯粹的数据展示与指令发送。
* **视图模块 (Views)：** 包含存储池拓扑图、数据集列表、硬盘状态监控（温度/通电时间/休眠状态）等独立页面。
* **通信总线 (Transport Controller)：**
    * **WebSocket Client：** 建立与后端的长连接，被动接收后端推送的最新 JSON 状态树，并更新 Vue 的响应式变量实现页面局部无刷新跳动。
    * **HTTP Client (Axios/Fetch)：** 负责发送具体的控制指令（如 POST 创数据集、休眠指定硬盘）和拉取历史趋势数据。
* **可视化图表 (Charts)：** 接收后端的时序 JSON 数据，渲染容量增长曲线或硬盘温度折线图。

### 2. 后端服务核心层 (API & Router Layer)
**技术栈：** Python + FastAPI
**核心功能：** 系统的交通枢纽，处理内外交互与数据校验。
* **RESTful 路由控制器 (HTTP Routers)：** 对外暴露接口（如 `/api/pool/create`、`/api/metrics/history`），处理前端发来的主动控制请求。
* **WebSocket 管理器 (WS Manager)：** 维护一个活跃连接池（Active Connections）。当连接数 > 0 时，通知底层加速轮询；当连接断开时，降频保活。负责将内存状态机的数据广播给所有在线客户端。
* **数据校验中心 (Pydantic Schemas)：** 拦截所有进出后端的数据。无论是前端传来的 JSON，还是底层解析出的数据，都必须经过 Pydantic 的严格类型检查，确保系统内部绝对的数据安全。

### 3. 状态管理与时序持久层 (State & DB Layer)
**技术栈：** Pydantic (内存) + SQLModel (SQLite)
**核心功能：** 系统的“短期记忆”与“长期档案”，完美适配时间序列数据的提取需求。
* **全局内存状态机 (Memory State Cache)：** 一个驻留在后端的 Pydantic 单例对象树。它时刻保持着最新的 PVE 硬盘与 ZFS 状态。前端的所有读取请求都直接命中这里，实现毫秒级响应。
* **降采样持久化引擎 (Downsampling Engine)：** 独立于高频刷新之外的定时任务。例如每隔 10 分钟，抓取当前“内存状态机”的快照，提取关键的时序指标（温度、使用量、碎片率），将其转化为 SQLModel 对象。
* **SQLite 时序数据库：** 专门存储清洗后的时序数据。这为以后直接导出 DataFrame，进行硬盘寿命趋势或存储时空演变分析准备了极为纯净的数据源。

### 4. 调度与解析层 (Execution & Parser Layer)
**技术栈：** Python `asyncio` + `asyncssh`
**核心功能：** 系统与底层操作系统对话的“翻译官”和“调度员”。
* **异步轮询任务 (Background Poller)：** 一个基于 `asyncio` 的后台死循环。根据 WS 管理器传来的指令动态调整睡眠时间（例如有人看网页时 2s 一次，无人时 60s 一次），定期触发 SSH 指令。
* **SSH 连接池 (Connection Pool)：** 维持与 PVE 宿主机的长连接隧道，避免频繁握手。
* **命令构造与解析器 (Command & Parser)：**
    * 向下：将后端的逻辑动作拼接成安全的 Linux 命令（如 `zpool status`, `hdparm -y /dev/sda`, `smartctl -j`）。
    * 向上：接收宿主机返回的纯文本或 JSON，使用正则或直接反序列化，将其清洗并更新到“全局内存状态机”中。

### 5. 宿主机底层 (Host OS Layer)
**运行环境：** PVE 或通用 Linux
**核心功能：** 物理指令的最终执行地。
* **OpenSSH Server：** 接收来自 Web 容器的指令。
* **Wrapper 包装脚本 (Bash)：** 安全的最后一道防线。通过 `authorized_keys` 的 `ForceCommand` 限制，确保该 SSH 密钥只能执行 ZFS 和硬盘相关的只读或受限写操作，防止容器被攻破后引发宿主机灾难。
* **系统二进制工具链：** OpenZFS 工具集、`lsblk`、`smartmontools`、`hdparm`/`nvme-cli`。

