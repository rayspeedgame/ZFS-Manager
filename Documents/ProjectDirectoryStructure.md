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

## 当前与 dataset 功能直接相关的关键文件

- `backend/app/api/rest.py`
- `backend/app/services/poller.py`
- `backend/app/services/dataset_creator.py`
- `backend/app/services/dataset_property_updater.py`
- `backend/app/services/dataset_destroyer.py`
- `frontend/src/views/DatasetsView.js`
- `frontend/src/store/state.js`
- `frontend/src/styles.css`
