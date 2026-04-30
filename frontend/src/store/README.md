# frontend/src/store

This folder contains the frontend realtime state module.

## Files

- [state.js](./state.js)
  - opens the WebSocket connection
  - stores the latest snapshot
  - exposes connection state and reconnect behavior

## Purpose

At the moment this is intentionally lightweight. It behaves like a small custom
store until the project needs something heavier such as Pinia.
