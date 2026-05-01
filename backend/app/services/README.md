# backend/app/services

This folder contains backend runtime services.

## Files

- [poller.py](./poller.py)
  - drives scheduled state refresh
  - supports fixture mode and live SSH mode
  - caches section data independently
  - keeps last-good data on refresh failures
  - merges section caches into the shared in-memory state store

## Current behavior

The polling layer now separates refresh work by resource type:

- disks
- pools
- datasets
- properties

This makes it possible to update fast-changing data more frequently than slow
or expensive queries without changing the frontend contract.

## Future direction

This layer is the right place for:

- adaptive polling frequency
- on-demand detail refresh
- action orchestration
- task tracking
- audit and event logging
