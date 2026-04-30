# frontend/src/views

This folder contains page-level frontend views.

## Files

- [DashboardView.js](./DashboardView.js)
  - global summary and health overview
- [DisksView.js](./DisksView.js)
  - disk inventory table and detail drawer
- [PoolsView.js](./PoolsView.js)
  - pool table, topology, and property drawer
- [DatasetsView.js](./DatasetsView.js)
  - dataset inventory and property-source drawer

## Design direction

Each view should:

- consume the shared realtime snapshot
- derive presentation-friendly rows/cards locally
- keep resource details inside the right-hand drawer pattern
