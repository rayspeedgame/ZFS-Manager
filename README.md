# ZFS Manager

> [中文版本](./README.zh-CN.md)

ZFS Manager is a web console for managing remote ZFS hosts via SSH. The project consists of a FastAPI backend, a Vue 3 frontend, and a set of state polling and write operation services, aiming to consolidate common pool, dataset, and disk viewing and management into a single interface.

## Current Capabilities

- Real-time display of `disks`, `pools`, `datasets`, and overview summary
- WebSocket push for latest snapshots, REST-triggered forced refresh after write operations
- View pool topology, disk `by-id`, health status, and removable targets
- Modify pool properties, add topology devices, create, delete, and remove pools
- Configure root dataset properties when creating a pool
- Manage datasets / zvols
  - Tree inventory
  - Detail drawer
  - Grouped fixed and editable properties
  - Create, modify, delete
  - Optional snapshot display
- Edit backend settings in the web interface
  - SSH connection parameters
  - Polling frequency
  - Whether to fall back to fixture when SSH fails
  - SSH connection test
- Optional web login password
  - Disabled by default
  - When enabled, requires login page before accessing the main interface
- Full `force refresh` support in the top bar
- Built-in English and Chinese switching with persistent user language preference

## Contents

- [backend/README.md](./backend/README.md): Backend services, endpoints, polling, and SSH write pipeline
- [frontend/README.md](./frontend/README.md): Frontend views, components, login gate, settings page, and i18n
- [Documents/README.md](./Documents/README.md): Project documentation, structure documents, and maintenance notes

## Running

Backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Configuration

The backend prioritizes reading configuration from `backend/config/config.json`, with the example file located at `backend/config/config.example.json`.

Main configuration blocks:

- `poller`
  - `mode`
  - `fallback_to_fixture`
  - `interval_seconds`
  - `tick_seconds`
  - `pools_interval_seconds`
  - `datasets_interval_seconds`
  - `disks_interval_seconds`
  - `properties_interval_seconds`
- `ssh`
  - host, port, username, password, key, known_hosts, timeout, and keepalive
- `auth`
  - `enabled`
  - `password`

Environment variable overrides are also supported. After saving from the settings page, the backend will write back to the config file and hot-reload the runtime services.
