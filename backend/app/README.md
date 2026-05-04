# app

> [中文版本](./README.zh-CN.md)

`app/` is the main backend code directory, responsible for configuration loading, authentication, endpoint exposure, SSH queries, state polling, write operation execution, and snapshot output.

## Subdirectory Responsibilities

- `api/`: REST and WebSocket routes
- `core/`: Configuration, authentication, shared state, and other infrastructure
- `schemas/`: Pydantic data models
- `services/`: Pollers, aggregators, and write operation services
- `ssh/`: SSH command definitions, client, and parsers

## Main Execution Flow

- `main.py` creates the FastAPI application and starts the runtime during its lifecycle
- Runtime holds the current configuration and a set of long-lifecycle services
- `StatePoller` is responsible for scheduled refresh of various states and writes to `state_store`
- Write endpoints trigger a forced refresh after executing commands
- Settings endpoints rebuild the runtime after saving, so new configuration takes effect immediately
