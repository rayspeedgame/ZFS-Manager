# backend/app/ssh

This folder contains the execution and parsing layer for host interaction.

## Files

- [client.py](./client.py)
  - async SSH client wrapper
  - keepalive support
  - reconnect-on-disconnect behavior
- [commands.py](./commands.py)
  - centralized read-only host command definitions
- [parser.py](./parser.py)
  - transforms raw command output into structured dictionaries

## Design intent

This layer should stay host-facing and protocol-focused.

It is responsible for:

- command construction
- SSH execution
- output parsing

It should not contain API routing or UI-oriented formatting.
