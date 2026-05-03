# Project Directory Structure

```text
ZFS-Manager/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- ssh/
|   |-- scripts/
|   |-- tests/
|   |   `-- fixtures/
|   |-- config.example.json
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

## Frontend Refactor Notes

- `frontend/src/views/PoolsView.vue`
  - page container for pool selection, dialog state, live snapshot rebinding, and API calls
- `frontend/src/views/DatasetsView.vue`
  - page container for dataset selection, tree expansion, dialog state, and API calls
- `frontend/src/components/common/`
  - reusable property editors, result lists, command logs, plus shared drawer/dialog shells
- `frontend/src/components/pools/`
  - list panel, detail drawer, topology drawer, create wizard, dialog bundle, and config
- `frontend/src/components/datasets/`
  - tree table, detail drawer, create drawer, dialog bundle, and config
- `frontend/src/i18n/`
  - locale selection logic and translation bundles for English and Simplified Chinese

## Related Hotspots

- Pool writes
  - `backend/app/services/pool_creator.py`
  - `backend/app/services/topology_updater.py`
  - `backend/app/services/pool_destroyer.py`
  - `backend/app/services/pool_remover.py`
- Dataset writes
  - `backend/app/services/dataset_creator.py`
  - `backend/app/services/dataset_property_updater.py`
  - `backend/app/services/dataset_destroyer.py`
- Frontend state and API
  - `frontend/src/stores/app.js`
  - `frontend/src/store/state.js`
  - `frontend/src/services/api.js`
- Frontend internationalization
  - `frontend/src/i18n/index.js`
  - `frontend/src/i18n/messages.js`
  - `frontend/src/router/routes.js`
  - `frontend/src/components/app/AppTopbar.vue`
