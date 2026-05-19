from __future__ import annotations

from app.core.config import AppConfig, load_config, resolve_task_db_path
from app.services.dataset_creator import DatasetCreator
from app.services.dataset_destroyer import DatasetDestroyer
from app.services.dataset_property_updater import DatasetPropertyUpdater
from app.services.pool_creator import PoolCreator
from app.services.pool_destroyer import PoolDestroyer
from app.services.pool_remover import PoolRemover
from app.services.pool_scrubber import PoolScrubber
from app.services.poller import StatePoller
from app.services.property_updater import PoolPropertyUpdater
from app.services.snapshot_creator import SnapshotCreator
from app.services.snapshot_destroyer import SnapshotDestroyer
from app.services.snapshot_rollbacker import SnapshotRollbacker
from app.services.task_manager import TaskManager
from app.services.task_recovery import TaskRecoveryService, build_default_recovery_registry
from app.services.task_scheduler import TaskSchedulerService
from app.services.task_store import SQLiteTaskStore
from app.services.topology_updater import PoolTopologyUpdater


config: AppConfig
poller: StatePoller
dataset_creator: DatasetCreator
dataset_destroyer: DatasetDestroyer
pool_creator: PoolCreator
pool_destroyer: PoolDestroyer
pool_remover: PoolRemover
pool_scrubber: PoolScrubber
pool_property_updater: PoolPropertyUpdater
dataset_property_updater: DatasetPropertyUpdater
snapshot_creator: SnapshotCreator
snapshot_destroyer: SnapshotDestroyer
snapshot_rollbacker: SnapshotRollbacker
pool_topology_updater: PoolTopologyUpdater
task_manager: TaskManager
task_recovery_service: TaskRecoveryService
task_scheduler: TaskSchedulerService
_runtime_started = False


def _build_runtime(next_config: AppConfig) -> None:
    global config
    global poller
    global dataset_creator
    global dataset_destroyer
    global pool_creator
    global pool_destroyer
    global pool_remover
    global pool_scrubber
    global pool_property_updater
    global dataset_property_updater
    global snapshot_creator
    global snapshot_destroyer
    global snapshot_rollbacker
    global pool_topology_updater
    global task_manager
    global task_recovery_service
    global task_scheduler

    config = next_config
    poller = StatePoller(config)
    dataset_creator = DatasetCreator(config)
    dataset_destroyer = DatasetDestroyer(config)
    pool_creator = PoolCreator(config)
    pool_destroyer = PoolDestroyer(config)
    pool_remover = PoolRemover(config)
    pool_scrubber = PoolScrubber(config)
    pool_property_updater = PoolPropertyUpdater(config)
    dataset_property_updater = DatasetPropertyUpdater(config)
    snapshot_creator = SnapshotCreator(config)
    snapshot_destroyer = SnapshotDestroyer(config)
    snapshot_rollbacker = SnapshotRollbacker(config)
    pool_topology_updater = PoolTopologyUpdater(config)
    task_store = SQLiteTaskStore(resolve_task_db_path())
    task_manager = TaskManager(store=task_store)
    task_recovery_service = TaskRecoveryService(task_manager, build_default_recovery_registry())
    task_scheduler = TaskSchedulerService(
        store=task_store,
        task_manager=task_manager,
        task_recovery_service=task_recovery_service,
        pool_scrubber=pool_scrubber,
        snapshot_creator=snapshot_creator,
        snapshot_destroyer=snapshot_destroyer,
        refresh_state=poller.refresh_once,
    )


async def start_runtime() -> None:
    global _runtime_started
    await task_manager.startup()
    state = await poller.refresh_once()
    await task_recovery_service.recover_pending_tasks(state)
    await poller.start()
    await task_scheduler.startup()
    _runtime_started = True


async def stop_runtime() -> None:
    global _runtime_started
    await task_scheduler.shutdown()
    await dataset_creator.close()
    await dataset_destroyer.close()
    await pool_creator.close()
    await pool_destroyer.close()
    await pool_remover.close()
    await pool_scrubber.close()
    await pool_topology_updater.close()
    await pool_property_updater.close()
    await dataset_property_updater.close()
    await snapshot_creator.close()
    await snapshot_destroyer.close()
    await snapshot_rollbacker.close()
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
