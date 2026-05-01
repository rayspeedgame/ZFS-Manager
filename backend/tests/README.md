# backend/tests

This folder contains backend tests and parser fixtures.

## Files

- [conftest.py](./conftest.py)
  - test environment setup
  - forces fixture mode so local SSH config does not affect tests
- [test_parser.py](./test_parser.py)
  - parser coverage
- [test_api.py](./test_api.py)
  - REST endpoint coverage
  - snapshot contract coverage for `meta` and `data`
- [test_ws.py](./test_ws.py)
  - WebSocket coverage
  - live snapshot shape coverage
- [test_config.py](./test_config.py)
  - config model coverage
- [test_ssh_client.py](./test_ssh_client.py)
  - reconnect behavior coverage
- [fixtures/README.md](./fixtures/README.md)
  - sample command outputs used during parser development

## Testing approach

Tests default to fixture mode so they can validate:

- parser shape
- snapshot assembly
- decoupled polling outputs
- API compatibility

without requiring a real SSH target.
