# frontend/src/views

This folder contains page-level frontend views.

## Files

- [DashboardView.js](./DashboardView.js)
  - global summary and health overview
  - consumes backend summary data
- [DisksView.js](./DisksView.js)
  - disk inventory table and detail drawer
  - consumes backend-provided disk rows
- [PoolsView.js](./PoolsView.js)
  - pool table, topology, and property drawer
  - consumes backend-provided pool rows
- [DatasetsView.js](./DatasetsView.js)
  - dataset inventory and property-source drawer
  - consumes backend-provided dataset rows

## Design direction

Each view should:

- consume the shared realtime snapshot
- prefer backend-prepared rows over local relationship assembly
- keep resource details inside the right-hand drawer pattern
