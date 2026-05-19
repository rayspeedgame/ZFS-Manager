from __future__ import annotations

from fastapi import APIRouter

from app.api.routes.datasets import router as datasets_router
from app.api.routes.pools import router as pools_router
from app.api.routes.snapshots import router as snapshots_router
from app.api.routes.system import router as system_router
from app.api.routes.tasks import router as tasks_router

# Keep this module as the stable import point for app.main while the actual
# endpoint implementations live in smaller resource-oriented route modules.
router = APIRouter()
router.include_router(system_router)
router.include_router(tasks_router)
router.include_router(pools_router)
router.include_router(datasets_router)
router.include_router(snapshots_router)
