# backend/app/core

This folder contains shared backend runtime infrastructure.

## Files

- [config.py](./config.py)
  - loads config from `backend/config.json`
  - supports environment-variable overrides
  - exposes polling cadence settings and SSH settings
- [state.py](./state.py)
  - stores the latest validated snapshot in memory
  - exposes versioned waiting for WebSocket push updates

## Design intent

`core/` contains application-wide primitives, not feature-specific logic.

Examples:

- configuration loading
- global state
- future logging setup
- future dependency wiring
