# router

Frontend routing setup.

## Files

- `index.js`: creates the router with `createWebHashHistory()`
- `routes.js`: route metadata for `Dashboard`, `Disks`, `Pools`, and `Datasets`

The project still uses hash history so direct refreshes do not require backend SPA fallback handling.
