# 目录树

```text
ZFS-Manager/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ssh/
│   ├── scripts/
│   ├── tests/
│   │   └── fixtures/
│   ├── config.example.json
│   ├── config.json
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── app/
│   │   │   └── common/
│   │   ├── lib/
│   │   ├── router/
│   │   ├── store/
│   │   └── views/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── Documents/
    ├── agent.md
    ├── target.md
    ├── ProjectStruction.md
    └── ProjectDirectoryStructure.md
```

## 备注

- `frontend/dist/` 和 `frontend/node_modules/` 属于构建产物与依赖目录，不纳入项目结构说明
- 后端 `__pycache__` 也不纳入结构文档
