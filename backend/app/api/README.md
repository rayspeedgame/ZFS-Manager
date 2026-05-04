# api

> [中文版本](./README.zh-CN.md)

This layer exposes the latest snapshot in backend memory and control endpoints to the frontend.

## File Descriptions

- `rest.py`: HTTP endpoints for state read, settings management, authentication, and write operation entry points
- `ws.py`: WebSocket push for frontend real-time updates

## Current API Conventions

- `GET /api/state`: Returns complete application snapshot
- `POST /api/state/refresh`: Triggers a full backend refresh
- `GET /api/settings`: Reads current active configuration
- `PUT /api/settings`: Saves configuration and hot-reloads runtime
- `POST /api/settings/test-ssh`: Tests SSH connection with temporary parameters without saving configuration
- `GET /api/auth/status`: Returns whether login is enabled and current authentication status
- `POST /api/auth/login`: Login
- `POST /api/auth/logout`: Logout
- `POST /api/pools/{pool_name}/properties`: Modify pool properties
- `POST /api/pools/{pool_name}/topology`: Add topology devices
- `POST /api/pools`: Create pool
- `POST /api/pools/{pool_name}/destroy`: Delete pool
- `POST /api/pools/{pool_name}/remove`: Remove removable topology targets
- `POST /api/datasets`: Create dataset / zvol
- `POST /api/datasets/{dataset_name:path}/properties`: Modify dataset properties
- `POST /api/datasets/{dataset_name:path}/destroy`: Delete dataset

## Current Constraints

- Dataset routes use `{dataset_name:path}` to support multi-level names like `tank/data`
- All `/api/*` requests except public endpoints require authentication middleware
- Write operations actively refresh after completion to push real host state back to frontend as soon as possible
