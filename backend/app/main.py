from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.rest import router as rest_router
from app.api.ws import router as ws_router
from app.runtime import poller, pool_property_updater


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start the poller with one warm-up refresh so /docs shows live data quickly.
    await poller.refresh_once()
    await poller.start()
    try:
        yield
    finally:
        await pool_property_updater.close()
        await poller.stop()


app = FastAPI(
    title="ZFS Manager Backend",
    version="0.3.0",
    description="Stage 3 demo: state polling plus WebSocket streaming.",
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

app.include_router(rest_router)
app.include_router(ws_router)
