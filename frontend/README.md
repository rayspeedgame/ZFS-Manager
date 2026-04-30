# Stage 3 Frontend Skeleton

This frontend is intentionally minimal. It opens a WebSocket connection to the backend and renders the incoming JSON state directly.

## Expected commands

```bash
npm install
npm run dev
```

By default the app connects to `ws://127.0.0.1:8000/ws/state`.

You can override the backend port with:

```bash
VITE_BACKEND_PORT=8000
```
