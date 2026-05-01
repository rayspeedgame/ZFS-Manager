# frontend/src/store

This folder contains the frontend realtime state module.

## Files

- [state.js](./state.js)
  - opens the WebSocket connection
  - stores the latest snapshot
  - exposes reconnect behavior and transport state

## Purpose

This store remains intentionally lightweight. It manages transport concerns,
while freshness, source status, errors, and refresh cadence come from the
backend snapshot `meta`.
