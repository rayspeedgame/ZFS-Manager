from __future__ import annotations

from app.core.config import load_config
from app.services.pool_creator import PoolCreator
from app.services.pool_destroyer import PoolDestroyer
from app.services.pool_remover import PoolRemover
from app.services.poller import StatePoller
from app.services.property_updater import PoolPropertyUpdater
from app.services.topology_updater import PoolTopologyUpdater


config = load_config()
poller = StatePoller(config)
pool_creator = PoolCreator(config)
pool_destroyer = PoolDestroyer(config)
pool_remover = PoolRemover(config)
pool_property_updater = PoolPropertyUpdater(config)
pool_topology_updater = PoolTopologyUpdater(config)
