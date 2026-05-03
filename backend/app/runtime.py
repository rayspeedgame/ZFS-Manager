from __future__ import annotations

from app.core.config import load_config
from app.services.dataset_creator import DatasetCreator
from app.services.dataset_destroyer import DatasetDestroyer
from app.services.dataset_property_updater import DatasetPropertyUpdater
from app.services.pool_creator import PoolCreator
from app.services.pool_destroyer import PoolDestroyer
from app.services.pool_remover import PoolRemover
from app.services.poller import StatePoller
from app.services.property_updater import PoolPropertyUpdater
from app.services.topology_updater import PoolTopologyUpdater


config = load_config()
poller = StatePoller(config)
dataset_creator = DatasetCreator(config)
dataset_destroyer = DatasetDestroyer(config)
pool_creator = PoolCreator(config)
pool_destroyer = PoolDestroyer(config)
pool_remover = PoolRemover(config)
pool_property_updater = PoolPropertyUpdater(config)
dataset_property_updater = DatasetPropertyUpdater(config)
pool_topology_updater = PoolTopologyUpdater(config)
