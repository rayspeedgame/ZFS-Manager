from __future__ import annotations

from app.core.config import load_config
from app.services.poller import StatePoller
from app.services.property_updater import PoolPropertyUpdater


config = load_config()
poller = StatePoller(config)
pool_property_updater = PoolPropertyUpdater(config)
