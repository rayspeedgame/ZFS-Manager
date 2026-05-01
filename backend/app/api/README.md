# backend/app/api

This folder contains the transport layer of the backend.

## Files

- [rest.py](./rest.py)
  - REST endpoints for current application state
- [ws.py](./ws.py)
  - WebSocket endpoint for live state streaming

## Notes

The API layer stays intentionally thin. It should mostly:

- accept requests
- return validated snapshot data
- stream updated snapshots

Business logic belongs in `services/`, and SSH execution and parsing belong in
`ssh/`.
