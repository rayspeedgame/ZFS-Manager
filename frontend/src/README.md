# frontend/src

This folder contains the frontend application source.

## Structure

- [components/README.md](./components/README.md)
- [lib/README.md](./lib/README.md)
- [router/README.md](./router/README.md)
- [store/README.md](./store/README.md)
- [views/README.md](./views/README.md)
- [App.js](./App.js)
  - root application shell
- [main.js](./main.js)
  - mounts the Vue app
- [styles.css](./styles.css)
  - shared app styling

## Current role

The frontend acts as a realtime operations console backed by a structured
snapshot contract. Resource pages mostly render backend-provided rows rather
than rebuilding storage relationships in the browser.
