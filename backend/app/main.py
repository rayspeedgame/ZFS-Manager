from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.rest import router as rest_router
from app.api.ws import router as ws_router
from app.core.config import load_config
from app.services.poller import StatePoller


config = load_config()
poller = StatePoller(config)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Start the poller with one warm-up refresh so /docs shows live data quickly.
    await poller.refresh_once()
    await poller.start()
    try:
        yield
    finally:
        await poller.stop()


app = FastAPI(
    title="ZFS Manager Backend",
    version="0.3.0",
    description="Stage 3 demo: state polling plus WebSocket streaming.",
    lifespan=lifespan,
)

app.include_router(rest_router)
app.include_router(ws_router)
