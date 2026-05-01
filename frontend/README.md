# Frontend

This frontend is a Vue-based realtime operations console for ZFS-Manager.

It consumes the backend WebSocket stream and renders the current storage state
into a multi-view dashboard layout.

## Current Features

- left navigation shell
- top status bar
- WebSocket transport state
- SSH source and data-age indicators
- Dashboard view
- Disks view
- Pools view
- Datasets view
- right-side detail drawers
- development JSON panel

## Current data contract

The frontend now primarily consumes backend-prepared domain data from:

- `snapshot.data.summary`
- `snapshot.data.disks`
- `snapshot.data.pools`
- `snapshot.data.datasets`

Raw overview fields are still available for compatibility and debugging, but
the resource views no longer need to reconstruct relationships locally.

## Folder Map

```text
frontend/
|- src/            # application source
|- index.html      # entry document
|- package.json    # frontend dependencies and scripts
|- vite.config.js  # Vite configuration
`- README.md
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

## UI Direction

The frontend is intentionally moving toward a practical operations console:

- backend-driven state contract
- clear freshness and degradation cues
- summary cards for global health
- tables for comparison-heavy resource views
- drawers for object details
