from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest import router as rest_router
from app.api.ws import router as ws_router
from app import runtime
from app.core.auth import request_is_authenticated


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start the poller with one warm-up refresh so /docs shows live data quickly.
    await runtime.start_runtime()
    try:
        yield
    finally:
        await runtime.stop_runtime()


app = FastAPI(
    title="ZFS Manager Backend",
    version="1.1.1",
    description=(
        "Remote ZFS management API with state polling, WebSocket streaming, "
        "pool/dataset/snapshot operations, SMART monitoring, tasks, and schedules."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS":
        return await call_next(request)
    # Keep auth bootstrap and docs public so the frontend can discover whether
    # login is enabled before it tries to open the main application shell.
    public_paths = {
        "/api/auth/status",
        "/api/auth/login",
        "/api/health",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
    if path.startswith("/api") and path not in public_paths and not request_is_authenticated(request):
        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required."},
        )
    return await call_next(request)


app.include_router(rest_router)
app.include_router(ws_router)
