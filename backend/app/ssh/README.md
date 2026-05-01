# backend/app/ssh

This folder contains the execution and parsing layer for host interaction.

## Files

- [client.py](./client.py)
  - async SSH client wrapper
  - keepalive support
  - reconnect-on-disconnect behavior
- [commands.py](./commands.py)
  - centralized read-only host command definitions
  - split overview commands into core and properties groups for decoupled polling
- [parser.py](./parser.py)
  - transforms raw command output into structured dictionaries
  - supports both combined overview payloads and split core/property payloads

## Design intent

This layer stays host-facing and protocol-focused.

It is responsible for:

- command construction
- SSH execution
- output parsing

It should not contain API routing or UI-specific rendering behavior.
