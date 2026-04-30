# backend/app/services

This folder contains backend runtime services.

## Files

- [poller.py](./poller.py)
  - drives periodic state refresh
  - supports fixture mode and live SSH mode
  - updates the shared in-memory state store

## Future direction

This layer is the right place for:

- adaptive polling frequency
- action orchestration
- task tracking
- audit/event logging
