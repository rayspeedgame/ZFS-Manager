# backend/app

This is the backend application package.

## Responsibilities

- define API entry points
- load runtime configuration
- manage the in-memory snapshot store
- schedule polling work by resource category
- execute SSH commands
- parse host output into structured state
- assemble validated snapshots for REST and WebSocket consumers

## Subdirectories

- [api/README.md](./api/README.md)
- [core/README.md](./core/README.md)
- [schemas/README.md](./schemas/README.md)
- [services/README.md](./services/README.md)
- [ssh/README.md](./ssh/README.md)

## Main entry point

- [main.py](./main.py)
  - creates the FastAPI app
  - wires poller startup and shutdown into the app lifespan
  - includes REST and WebSocket routes
