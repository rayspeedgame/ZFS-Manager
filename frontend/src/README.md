# src

`src/` contains the Vue frontend source.

## Structure

- `App.vue`: root application shell
- `main.js`: app bootstrap
- `styles.css`: global shared styles
- `components/`: reusable UI pieces
- `lib/`: formatting helpers
- `router/`: route metadata and router creation
- `services/`: REST API calls
- `store/`: compatibility adapter layer
- `stores/`: Pinia stores
- `views/`: routed page components

## Current Notes

- The frontend should prefer rendering backend-prepared structures instead of reconstructing business state on its own.
- Dataset depth, parentage, short names, and tree order should continue to come from backend snapshot data whenever available.
