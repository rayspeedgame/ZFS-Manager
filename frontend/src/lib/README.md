# frontend/src/lib

This folder contains small pure utility helpers.

## Files

- [formatters.js](./formatters.js)
  - byte formatting
  - percent formatting
  - datetime formatting
  - legacy source-label helpers

## Note

Several row-shaping helpers were intentionally moved out of the frontend during
this stage. Resource preparation now happens in the backend so views can mostly
render `snapshot.data.*` directly.
