# backend/app/api

This folder contains the transport layer of the backend.

## Files

- [rest.py](./rest.py)
  - REST endpoints for current application state
- [ws.py](./ws.py)
  - WebSocket endpoint for live state streaming

## Notes

The API layer should stay thin. It should mostly:

- accept requests
- return validated state
- stream updates

Business logic should remain in `services/` and parsing/execution should remain
in `ssh/`.
