# Frontend

This frontend is a Vue-based realtime operations console for ZFS-Manager.

It consumes the backend WebSocket stream and renders the current storage state
into a multi-view dashboard layout.

## Current Features

- left navigation shell
- top status bar
- live connection state
- Dashboard view
- Disks view
- Pools view
- Datasets view
- right-side detail drawers
- development JSON panel

## Folder Map

```text
frontend/
├── src/            # application source
├── index.html      # entry document
├── package.json    # frontend dependencies and scripts
├── vite.config.js  # Vite configuration
└── README.md
```

See:

- [src/README.md](./src/README.md)

## Install

```bash
npm install
```

## Run

```bash
npm run dev
```

The app expects the backend to be running on port `8000` by default.

WebSocket target:

- `ws://127.0.0.1:8000/ws/state`

You can override the port with:

```bash
VITE_BACKEND_PORT=8000
```

## Build

```bash
npm run build
```

## Current UI Direction

The frontend is intentionally moving toward a modern operations console:

- dense but readable information layout
- neutral dark theme
- summary cards for global status
- tables for comparison-heavy resource views
- drawers for object details

This is the first structured UI layer, not the final polished design.
