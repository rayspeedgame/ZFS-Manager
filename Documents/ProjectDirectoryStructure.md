# Project Directory Structure

```text
ZFS-Manager/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  └─ ssh/
│  ├─ scripts/
│  ├─ tests/
│  │  └─ fixtures/
│  ├─ config.example.json
│  ├─ config.json
│  ├─ README.md
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ lib/
│  │  ├─ router/
│  │  ├─ store/
│  │  └─ views/
│  ├─ README.md
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ Documents/
│  ├─ README.md
│  ├─ agent.md
│  ├─ target.md
│  ├─ ProjectStruction.md
│  └─ ProjectDirectoryStructure.md
└─ README.md
```

## 与 pool 功能直接相关的文件

- `backend/app/api/rest.py`
- `backend/app/services/poller.py`
- `backend/app/services/pool_creator.py`
- `backend/app/services/pool_destroyer.py`
- `backend/app/services/pool_remover.py`
- `backend/app/services/topology_updater.py`
- `frontend/src/views/PoolsView.js`
- `frontend/src/store/state.js`
- `frontend/src/styles.css`
