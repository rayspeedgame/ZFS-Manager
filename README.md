# ZFS-Manager

ZFS-Manager is a web-based management console for ZFS storage on a PVE host.
The current codebase already includes:

- a Python backend that connects to a host through SSH
- parsers for disk, zpool, and dataset state
- an in-memory state machine refreshed by a background poller
- REST and WebSocket APIs built with FastAPI
- a Vue frontend skeleton that renders live state in a modern operations-style UI

The project is being built in stages. At the moment, the architecture and live
data flow are already working end to end.

## Current Status

Implemented:

- SSH command execution with `asyncssh`
- multi-command storage overview collection
- parsing for:
  - `lsblk`
  - `findmnt`
  - `blkid`
  - `zpool status`
  - `zpool list/get`
  - `zfs list/get`
- FastAPI state API
- WebSocket state streaming
- Vue control-panel skeleton with:
  - Dashboard
  - Disks
  - Pools
  - Datasets

Planned next:

- richer frontend views and filtering
- resource detail editing flows
- dataset and pool management actions
- Docker packaging and deployment workflow

## Repository Structure

```text
ZFS-Manager/
├── backend/      # FastAPI backend, SSH integration, parsers, tests
├── frontend/     # Vue frontend skeleton and live WebSocket client
├── Documents/    # Planning notes and original design documents
└── README.md
```

More detailed directory notes live inside each major folder:

- [backend/README.md](./backend/README.md)
- [backend/app/README.md](./backend/app/README.md)
- [frontend/README.md](./frontend/README.md)
- [frontend/src/README.md](./frontend/src/README.md)
- [Documents/README.md](./Documents/README.md)

## Architecture Overview

### Backend flow

1. The poller gathers disk, pool, and dataset information.
2. Raw command output is parsed into structured Python dictionaries.
3. Parsed data is validated into Pydantic models.
4. The latest validated snapshot is stored in the in-memory state store.
5. REST returns the latest snapshot on demand.
6. WebSocket pushes updated snapshots to connected frontend clients.

### Frontend flow

1. The app opens a WebSocket connection to the backend.
2. Incoming snapshots are stored in a simple client-side state module.
3. Views derive dashboard cards, tables, and detail drawers from that snapshot.
4. The UI updates automatically whenever a new state payload arrives.

## Backend Quick Start

See [backend/README.md](./backend/README.md) for full details.

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

The current test suite covers:

- parser behavior
- config loading
- API responses
- WebSocket streaming
- SSH reconnection handling

## Design Direction

The UI is intentionally moving toward a modern operations console:

- left navigation
- top status bar
- resource-focused views
- right-side detail drawers
- live state as the primary source of truth

This is meant to become a usable management tool, not just a JSON viewer.
