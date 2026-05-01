# backend/scripts

This folder contains local development and debugging helpers.

## Files

- [debug_ssh_parser.py](./debug_ssh_parser.py)
  - runs parser logic against fixture files
  - or executes commands through SSH and prints parsed JSON

## Use case

This is useful when developing parsers or SSH command groupings without running
the full FastAPI app.
