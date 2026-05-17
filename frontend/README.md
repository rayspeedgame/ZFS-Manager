# Frontend

> [中文版本](./README.zh-CN.md)

The frontend uses Vue 3 single-file components on Vite, `vue-router`, Pinia, and `vue-i18n`. It consumes backend snapshots, renders the storage management UI, exposes task records and schedules, and wraps high-risk writes into clear, confirmable flows.

## Main Views

- `Dashboard`
  - Real-time summary cards and health overview
- `Disks`
  - Disk inventory, partitions, filesystem labels, and pool ownership
- `Pools`
  - Pool overview, topology browsing, property editing, create, remove, destroy, and `scrub`
- `Datasets`
  - Dataset / zvol tree, snapshot toggle, property editing, create, and destroy
- `Schedules`
  - Scheduled `scrub` management and scheduled snapshot placeholder
- `Tasks`
  - Task records, live status, progress, filters, pagination, and command logs
- `Settings`
  - Backend SSH, polling, and web login settings

## Current Architecture

- `src/App.vue`
  - Application shell and login gate selection based on auth status
- `src/components/app`
  - Sidebar, topbar, and login gate shell components
- `src/components/common`
  - Shared drawer, dialog, property editor, and command-result components
- `src/components/pools`
  - Pool list, drawer, topology, and create-flow components
- `src/components/datasets`
  - Dataset tree, drawer, and create-flow components
- `src/i18n/index.js`
  - Locale initialization, browser language detection, and local persistence
- `src/i18n/messages/en-US/` and `src/i18n/messages/zh-CN/`
  - Module-split translation resources
- `src/router/routes.js`
  - Route metadata for dashboard, disks, pools, datasets, schedules, tasks, and settings
- `src/stores/app.js`
  - WebSocket lifecycle, snapshot cache, auth state, and refresh actions
- `src/stores/tasks.js`
  - Task records list, selected detail, pagination, status filter, and periodic refresh logic
- `src/services/api.js`
  - REST writes, task APIs, task schedule APIs, settings APIs, and auth APIs
- `src/store/state.js`
  - Compatibility adapter for legacy `useAppState()` shape

## Internationalization Notes

- Supports `en-US` and `zh-CN`
- First load selects locale from browser language
- User language preference is written to `localStorage`
- Text resources are split by language and module
- New user-visible text should preferentially use `useI18n()` instead of hardcoded strings

## Authentication Notes

- Web password login is disabled by default
- When enabled, the frontend first requests `/api/auth/status`
- `AppLoginGate.vue` is shown when unauthenticated
- After successful login, the frontend establishes the WebSocket connection and enters the main UI

## Development

```bash
npm install
npm run dev
npm run build
```
