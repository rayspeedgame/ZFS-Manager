# Frontend

> [中文版本](./README.zh-CN.md)

The frontend uses Vue 3 single-file components, running on Vite, `vue-router`, Pinia, and `vue-i18n`. It is responsible for consuming backend snapshots, rendering the storage management interface, and wrapping high-risk write operations into clear, confirmable flows.

## Main Views

- `Dashboard`
  - Real-time summary cards and health overview
- `Disks`
  - Disk inventory, partitions, filesystem labels, and pool ownership
- `Pools`
  - Pool overview, topology browsing, property editing, create, remove, and destroy
- `Datasets`
  - Dataset / zvol tree, snapshot toggle, property editing, create and destroy
- `Settings`
  - Backend SSH, polling, and web login settings

## Current Architecture

- `src/App.vue`
  - Application shell, decides whether to show login page or main interface based on login status
- `src/components/app`
  - Shell components including sidebar, topbar, and login gate
- `src/components/common`
  - Common drawer, dialog, property editor, and command result components
- `src/components/pools`
  - Pool-specific list, drawer, topology, and create flow components
- `src/components/datasets`
  - Dataset-specific tree, drawer, and create flow components
- `src/i18n/index.js`
  - Locale initialization, browser language detection, local persistence
- `src/i18n/messages.js`
  - Central translation entry, aggregates language resources
- `src/i18n/messages/en-US/` and `src/i18n/messages/zh-CN/`
  - Module-split translation resources
- `src/router/routes.js`
  - Top-level route metadata, uses translation keys instead of hardcoded text
- `src/stores/app.js`
  - WebSocket lifecycle, snapshot cache, auth state, and refresh actions
- `src/services/api.js`
  - REST write requests, settings endpoints, and auth endpoints
- `src/store/state.js`
  - Compatibility adapter for legacy `useAppState()` shape

## Internationalization Notes

- Currently supports `en-US` and `zh-CN`
- First load selects language based on browser language
- User language preference is written to `localStorage`
- Text resources are split by language and module; when extending new pages, prioritize appending to the corresponding module
- New visible text should preferentially use `useI18n()`, avoid hardcoding

## Authentication Notes

- Web password login is disabled by default
- When enabled, frontend first requests `/api/auth/status`
- Shows `AppLoginGate.vue` when not logged in
- After successful login, establishes WebSocket connection and enters main interface

## Development

```bash
npm install
npm run dev
npm run build
```
