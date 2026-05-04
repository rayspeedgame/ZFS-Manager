# ZFS Manager

> [中文版本](./README.zh-CN.md)

A web-based management console for remote ZFS hosts via SSH. ZFS Manager brings common pool, dataset, and disk operations into a single, intuitive interface — no need to drop to the shell for everyday tasks.

## Features

### Pool Management
- Live pool overview with usage, health, and capacity metrics
- Visual topology browsing with device status
- Create, edit properties, add/remove devices, and destroy pools
- Configure root dataset properties during pool creation

### Dataset & Zvol Management
- Hierarchical tree view with expandable dataset structure
- Create, modify, and destroy datasets and zvols
- Grouped property display with inline editing
- Optional snapshot visibility toggle

### Disk Monitoring
- Disk inventory with model, type, and health status
- Partition and filesystem information
- Pool ownership association

### Real-time Updates
- WebSocket-powered live state synchronization
- Force refresh from the top bar
- Automatic refresh after write operations

### Multi-language Support
- Built-in English and Simplified Chinese
- Browser language auto-detection
- Persistent language preference

### Security
- Optional web login with password protection
- Cookie-based session management

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3, Vite, vue-router, Pinia, vue-i18n |
| Backend | FastAPI, Pydantic, async SSH |
| Transport | REST (writes), WebSocket (live updates) |
| Communication | SSH to remote ZFS host |

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Documentation

- [Backend Details](./backend/README.md)
- [Frontend Details](./frontend/README.md)
- [Project Documents](./Documents/README.md)
