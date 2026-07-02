# Agent Guide

> [中文版本](./agent.zh-CN.md)

This note helps a new contributor understand where data comes from, where writes go, and which areas are easiest to break.

## Stack

- Backend: FastAPI + Pydantic + async SSH
- Frontend: Vue 3 + Vite + `vue-router` + Pinia + `vue-i18n`
- Transport: REST for writes, WebSocket for live snapshots

## Core Concepts

### Snapshot-first UI

- The frontend should prefer `snapshot.data.*` from the backend instead of rebuilding ZFS state locally.
- Dataset depth, parentage, short names, and ordering should come from backend-prepared fields whenever possible.

### Client-aware polling

- The poller automatically switches between active (fast) and idle (slow) refresh cadences.
- A `ClientTracker` singleton in `backend/app/core/client_tracker.py` counts connected WebSocket clients.
- Mode detection runs at a fixed 1-second interval — independent of the configurable tick/refresh intervals.
- When a browser connects, the poller switches to active intervals and forces an immediate full refresh.
- When the last browser disconnects, the poller drops to the configured idle intervals.
- Active and idle intervals for each job (pools, datasets, disks, properties) are configurable in the Settings UI.
- The wake-up interval (`tick_seconds` / `idle_tick_seconds`) controls how often `refresh_once()` is called; mode detection always runs at 1 Hz.

### Write flow contract

Most pool and dataset mutations follow the same lifecycle:

1. Validate user input in the frontend.
2. Submit a REST write request.
3. Execute the command through backend SSH services.
4. Trigger an immediate refresh on success or partial success.
5. Show both a summary and detailed command results.

### View containers after the refactor

- `frontend/src/views/PoolsView.vue`
  - owns selected pool state, dialog state, live snapshot rebinding, and dirty-draft guards
- `frontend/src/views/DatasetsView.vue`
  - owns selected dataset state, tree expansion, create/destroy flows, and dirty-draft guards
- `frontend/src/components/common/`
  - hosts shared property editors, command result rendering, and log presentation
- `frontend/src/components/pools/` and `frontend/src/components/datasets/`
  - host UI-only workflow pieces that emit events back to the page containers

### Locale system

- `frontend/src/i18n/index.js` chooses the initial locale from `localStorage` first, then browser language, then fallback locale.
- `frontend/src/i18n/messages.js` holds grouped translation keys for shell, routes, common UI, dashboard, pools, and datasets.
- Route metadata should use `labelKey` and `descriptionKey` so navigation and view headers react to locale changes.
- When adding UI copy, prefer translation keys over raw strings unless the value is a domain-native token that should stay verbatim.

## Key Maintenance Entry Points

- Read path
  - `backend/app/services/poller.py`
  - `backend/app/core/client_tracker.py`
  - `backend/app/ssh/parser.py`
  - `frontend/src/stores/app.js`
- Write path
  - `backend/app/api/rest.py`
  - `backend/app/services/pool_creator.py`
  - `backend/app/services/topology_updater.py`
  - `backend/app/services/dataset_creator.py`
  - `backend/app/services/dataset_property_updater.py`
  - `backend/app/services/dataset_destroyer.py`
  - `frontend/src/services/api.js`

## Common Footguns

- A live snapshot can arrive while the user is editing a form, so the page containers must guard dirty drafts before rebinding new snapshot data.
- Dataset names may contain `/`, so REST routes must keep using `{dataset_name:path}`.
- `Show snapshots` stays opt-in because large snapshot sets add a lot of UI noise.
- `frontend/src/store/state.js` is still a compatibility layer; new state work should prefer the Pinia store in `frontend/src/stores/app.js`.
- Locale-sensitive labels inside long-lived arrays should usually be wrapped in `computed()` so switching languages updates the active view immediately.
- The poller's wake-up interval (`tick_seconds`) must be ≤ the fastest job refresh interval; otherwise, jobs with short refresh intervals are effectively throttled by the tick.
