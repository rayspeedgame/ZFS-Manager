# ZFS-Manager

ZFS-Manager is a web-based management console for ZFS storage on a Linux host.
The project now has a working end-to-end architecture with:

- a Python backend that connects to a host through SSH
- structured parsing for disk, pool, and dataset state
- an in-memory snapshot store with retained last-good data
- REST and WebSocket APIs built with FastAPI
- a Vue frontend that renders backend-provided domain data
- decoupled polling schedules for different resource types

## Current Stage

Implemented in this stage:

- SSH command execution with `asyncssh`
- parsing for:
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status`
  - `zpool list`
  - `zpool get`
  - `zfs list`
  - `zfs get`
- backend snapshot model split into `meta` and `data`
- stale-data behavior which keeps the last successful snapshot on SSH failure
- backend-generated `summary`, `disks`, `pools`, and `datasets` data for the UI
- decoupled polling intervals for:
  - disks
  - pools
  - datasets
  - properties
- FastAPI state API
- WebSocket state streaming
- Vue control-panel UI with:
  - Dashboard
  - Disks
  - Pools
  - Datasets

Planned next:

- action flows for pool and dataset management
- richer filtering and search
- authentication and deployment packaging
- long-term observability and audit features

## Repository Structure

```text
ZFS-Manager/
|- backend/      # FastAPI backend, SSH integration, polling, tests
|- frontend/     # Vue frontend and realtime state client
|- Documents/    # planning notes and architecture references
`- README.md
```

More detailed notes live in:

- [backend/README.md](./backend/README.md)
- [frontend/README.md](./frontend/README.md)
- [Documents/README.md](./Documents/README.md)

## Architecture Overview

### Backend flow

1. The poller schedules refresh jobs for disks, pools, datasets, and properties.
2. SSH commands are executed in grouped read-only batches.
3. Raw host output is parsed into structured Python dictionaries.
4. Parsed sections are merged into a validated `AppState` snapshot.
5. `meta` describes freshness, source status, errors, and refresh plan.
6. `data` exposes summary and UI-ready resource rows plus raw overview data.
7. REST returns the latest snapshot on demand.
8. WebSocket pushes updated snapshots to connected frontend clients.

### Frontend flow

1. The app opens a WebSocket connection to the backend.
2. Incoming snapshots are stored in a lightweight client-side store.
3. Views consume backend-provided domain rows from `snapshot.data.*`.
4. The UI keeps rendering the last successful data even when SSH becomes stale.

## Backend Quick Start

See [backend/README.md](./backend/README.md) for details.

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Useful URLs:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- State API: [http://127.0.0.1:8000/api/state](http://127.0.0.1:8000/api/state)
- WebSocket: `ws://127.0.0.1:8000/ws/state`

## Frontend Quick Start

See [frontend/README.md](./frontend/README.md) for more detail.

```bash
cd frontend
npm install
npm run dev
```

Then open the local Vite URL, usually:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Configuration

Backend runtime configuration is documented in:

- [backend/config.example.json](./backend/config.example.json)
- [backend/app/core/README.md](./backend/app/core/README.md)

Important note:

- `backend/config.json` is intentionally ignored because it may contain private
  SSH credentials for the target host.

## Testing

Backend tests:

```bash
cd backend
pytest
```

Current automated coverage includes:

- parser behavior
- config loading
- API responses
- WebSocket streaming
- SSH reconnect handling
- snapshot shape for new `meta/data` fields

## Design Direction

The current architecture is intentionally centered around the backend as the
source of truth:

- backend-owned domain models
- stale-safe snapshots
- thin transport layer
- frontend views that mostly render prepared data
- polling that can evolve per resource without reshaping the UI contract
