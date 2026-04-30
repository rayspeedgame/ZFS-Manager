# backend/app

This is the backend application package.

## Responsibilities

- define API entry points
- load configuration
- manage in-memory state
- run the polling loop
- execute SSH commands
- parse host output into structured state

## Subdirectories

- [api/README.md](./api/README.md)
- [core/README.md](./core/README.md)
- [schemas/README.md](./schemas/README.md)
- [services/README.md](./services/README.md)
- [ssh/README.md](./ssh/README.md)

## Main entry point

- [main.py](./main.py)
  - creates the FastAPI app
  - wires poller startup/shutdown into the app lifespan
  - includes REST and WebSocket routes
