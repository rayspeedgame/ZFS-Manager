from __future__ import annotations

from app.core.config import AppConfig, load_config
from app.services.dataset_creator import DatasetCreator
from app.services.dataset_destroyer import DatasetDestroyer
from app.services.dataset_property_updater import DatasetPropertyUpdater
from app.services.pool_creator import PoolCreator
from app.services.pool_destroyer import PoolDestroyer
from app.services.pool_remover import PoolRemover
from app.services.poller import StatePoller
from app.services.property_updater import PoolPropertyUpdater
from app.services.topology_updater import PoolTopologyUpdater


config: AppConfig
poller: StatePoller
dataset_creator: DatasetCreator
dataset_destroyer: DatasetDestroyer
pool_creator: PoolCreator
pool_destroyer: PoolDestroyer
pool_remover: PoolRemover
pool_property_updater: PoolPropertyUpdater
dataset_property_updater: DatasetPropertyUpdater
pool_topology_updater: PoolTopologyUpdater
_runtime_started = False


def _build_runtime(next_config: AppConfig) -> None:
    global config
    global poller
    global dataset_creator
    global dataset_destroyer
    global pool_creator
    global pool_destroyer
    global pool_remover
    global pool_property_updater
    global dataset_property_updater
    global pool_topology_updater

    config = next_config
    poller = StatePoller(config)
    dataset_creator = DatasetCreator(config)
    dataset_destroyer = DatasetDestroyer(config)
    pool_creator = PoolCreator(config)
    pool_destroyer = PoolDestroyer(config)
    pool_remover = PoolRemover(config)
    pool_property_updater = PoolPropertyUpdater(config)
    dataset_property_updater = DatasetPropertyUpdater(config)
    pool_topology_updater = PoolTopologyUpdater(config)


async def start_runtime() -> None:
    global _runtime_started
    await poller.refresh_once()
    await poller.start()
    _runtime_started = True


async def stop_runtime() -> None:
    global _runtime_started
    await dataset_creator.close()
    await dataset_destroyer.close()
    await pool_creator.close()
    await pool_destroyer.close()
    await pool_remover.close()
    await pool_topology_updater.close()
    await pool_property_updater.close()
    await dataset_property_updater.close()
    await poller.stop()
    _runtime_started = False


async def reload_runtime(next_config: AppConfig | None = None) -> AppConfig:
    started = _runtime_started
    if started:
        await stop_runtime()
    _build_runtime(next_config or load_config())
    if started:
        await start_runtime()
    return config


_build_runtime(load_config())
