# backend/app/schemas

This folder contains Pydantic models used by the backend.

## Files

- [zfs_state.py](./zfs_state.py)
  - models the application snapshot returned by REST and WebSocket

## Purpose

These schemas make the state shape explicit and keep the API contract stable
while the parser and frontend evolve.
