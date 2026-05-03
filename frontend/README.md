# Frontend

The frontend uses Vue 3 single-file components on top of Vite, `vue-router`, Pinia, and `vue-i18n`.
It consumes backend snapshots, renders the storage UI, and keeps risky write flows explicit and reviewable.

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
- `src/components/app`
  - shell components including the refresh action and locale switcher
- `src/components/common`
  - shared drawer, dialog, property, and command-result primitives
- `src/components/pools`
  - pool-only list, drawer, topology, and create workflow components
- `src/components/datasets`
  - dataset-only tree, drawer, and create workflow components
- `src/i18n/index.js`
  - locale bootstrap, browser-language detection, and local storage persistence
- `src/i18n/messages.js`
  - translation resources grouped by module such as `app`, `routes`, `common`, `dashboard`, `pools`, and `datasets`
- `src/router/index.js`
  - router bootstrap using `createWebHashHistory()`
- `src/router/routes.js`
  - top-level route metadata and component mapping using `labelKey` and `descriptionKey`
- `src/stores/app.js`
  - Pinia app store for WebSocket lifecycle, snapshots, and refresh actions
- `src/services/api.js`
  - REST write operations for pools and datasets
- `src/store/state.js`
  - compatibility adapter that exposes the old `useAppState()` shape while delegating to Pinia and the API service
- `src/views/PoolsView.vue`
  - pool page container, live snapshot rebinding, create wizard orchestration, and write actions
- `src/views/DatasetsView.vue`
  - dataset page container, live snapshot rebinding, and write orchestration
- `src/styles.css`
  - shared layout, table, drawer, dialog, locale switcher, and responsive styles

## Internationalization Notes

- The app currently ships with `en-US` and `zh-CN`.
- First load chooses Chinese for `zh*` browser languages and English otherwise.
- User locale changes are persisted in `localStorage`, so refreshes keep the selected language.
- The topbar locale switcher lives to the left of the `Refresh` button.
- New visible UI copy should use translation keys instead of hardcoded strings.
- Route metadata now stores keys, not raw labels, so shell navigation stays reactive when the locale changes.

## Interaction Rules

- Every destructive or high-risk action must go through an explicit confirmation dialog.
- Submissions should show a clear loading state.
- Results should include both a human summary and SSH command log details when available.
- After write actions, the frontend should re-sync using `/api/state` or `/api/state/refresh`.
- Live snapshot updates must not overwrite in-progress form edits; page containers keep dirty-draft guards for this.
- Locale changes should update visible shell and page copy without requiring a route reload.

## Development

```bash
npm install
npm run dev
npm run build
```
