# Frontend

The frontend now uses standard Vue 3 single-file components on top of Vite, `vue-router`, and Pinia.
It consumes backend snapshots, renders the storage UI, and keeps dangerous write flows explicit and reviewable.

## Main Views

- `Dashboard`
  - live summary cards and pool health overview
- `Disks`
  - disk inventory, partitions, filesystem labels, and pool membership
- `Pools`
  - pool overview, topology browser, property editing, create/remove/destroy flows
- `Datasets`
  - dataset and zvol tree inventory, snapshot toggle, property editing, create/destroy flows

## Current Architecture

- `src/App.vue`
  - application shell, sidebar, topbar, and routed page outlet
- `src/router/index.js`
  - router bootstrap using `createWebHashHistory()`
- `src/router/routes.js`
  - top-level route metadata and component mapping
- `src/stores/app.js`
  - Pinia app store for WebSocket lifecycle, snapshots, and refresh actions
- `src/services/api.js`
  - REST write operations for pools and datasets
- `src/store/state.js`
  - compatibility adapter that exposes the old `useAppState()` shape while delegating to Pinia and the API service
- `src/views/PoolsView.vue`
  - pool-heavy workflows and topology management
- `src/views/DatasetsView.vue`
  - dataset-heavy workflows and tree presentation
- `src/styles.css`
  - shared layout, table, drawer, dialog, and responsive styles

## Interaction Rules

- Every destructive or high-risk action must go through an explicit confirmation dialog.
- Submissions should show a clear loading state.
- Results should include both a human summary and SSH command log details when available.
- After write actions, the frontend should re-sync using `/api/state` or `/api/state/refresh`.

## Development

```bash
npm install
npm run dev
```
