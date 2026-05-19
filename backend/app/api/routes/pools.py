from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import runtime
from app.api.common import (
    build_multi_result_task_message,
    build_single_result_task_message,
    task_log_from_multi_result,
    task_log_from_single_result,
)
from app.api.validators import (
    pool_has_active_scrub,
    require_pool,
    validate_pool_creation,
    validate_pool_removal,
    validate_topology_additions,
)
from app.core.state import state_store
from app.schemas.pool_create import PoolCreateRequest, PoolCreateResponse
from app.schemas.pool_destroy import PoolDestroyResponse
from app.schemas.pool_remove import PoolRemoveRequest, PoolRemoveResponse
from app.schemas.pool_scrub import PoolScrubResponse
from app.schemas.property_update import PoolPropertyUpdateRequest, PoolPropertyUpdateResponse
from app.schemas.topology_update import PoolTopologyUpdateRequest, PoolTopologyUpdateResponse

router = APIRouter(prefix="/api")


@router.post("/pools", response_model=PoolCreateResponse, tags=["pools"])
async def create_pool(payload: PoolCreateRequest) -> PoolCreateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool creation requires SSH mode.")

    state = await state_store.get_state()
    validate_pool_creation(payload=payload, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Create pool {payload.name}",
        kind="pool.create",
        scope_type="pool",
        scope_name=payload.name,
        message="Queued pool creation.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Creating pool {payload.name}...", progress=25)

    result = await runtime.pool_creator.create_pool(payload)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Pool writes always force a full refresh so the response reflects
        # the host's real post-command state instead of local assumptions.
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    finalized = result.model_copy(update={"task_id": task.id, "refreshed": refreshed, "refresh_error": refresh_error})
    await runtime.task_manager.mark_finished(
        task.id,
        success=result.success,
        message=build_single_result_task_message(
            success=result.success,
            success_text=f"Pool {payload.name} created.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=payload.name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/pools/{pool_name}/destroy", response_model=PoolDestroyResponse, tags=["pools"])
async def destroy_pool(pool_name: str) -> PoolDestroyResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool destroy requires SSH mode.")

    state = await state_store.get_state()
    require_pool(pool_name=pool_name, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Destroy pool {pool_name}",
        kind="pool.destroy",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued pool destroy.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Destroying pool {pool_name}...", progress=25)

    result = await runtime.pool_destroyer.destroy_pool(pool_name)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    finalized = result.model_copy(update={"task_id": task.id, "refreshed": refreshed, "refresh_error": refresh_error})
    await runtime.task_manager.mark_finished(
        task.id,
        success=result.success,
        message=build_single_result_task_message(
            success=result.success,
            success_text=f"Pool {pool_name} destroyed.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=pool_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/pools/{pool_name}/remove", response_model=PoolRemoveResponse, tags=["pools"])
async def remove_pool_target(
    pool_name: str,
    payload: PoolRemoveRequest,
) -> PoolRemoveResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology removal requires SSH mode.")

    state = await state_store.get_state()
    target = validate_pool_removal(pool_name=pool_name, payload=payload, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Remove {payload.command_target} from pool {pool_name}",
        kind="pool.remove",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued pool topology removal.",
        metadata={"command_target": payload.command_target},
    )
    await runtime.task_manager.mark_running(
        task.id,
        message=f"Removing {payload.command_target} from pool {pool_name}...",
        progress=25,
    )

    result = await runtime.pool_remover.remove_target(
        pool=pool_name,
        command_target=payload.command_target,
        display_label=str(target.get("displayLabel") or payload.command_target),
        target_type=str(target.get("targetType") or "device"),
        vdev_class=str(target.get("vdevClass") or "data"),
        layout=str(target.get("layout") or "stripe"),
    )

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    finalized = result.model_copy(update={"task_id": task.id, "refreshed": refreshed, "refresh_error": refresh_error})
    await runtime.task_manager.mark_finished(
        task.id,
        success=result.success,
        message=build_single_result_task_message(
            success=result.success,
            success_text=f"Removed {payload.command_target} from pool {pool_name}.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=payload.command_target, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/pools/{pool_name}/properties", response_model=PoolPropertyUpdateResponse, tags=["pools"])
async def update_pool_properties(
    pool_name: str,
    payload: PoolPropertyUpdateRequest,
) -> PoolPropertyUpdateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool property updates require SSH mode.")

    if not payload.changes:
        raise HTTPException(status_code=400, detail="No property changes were provided.")

    task = await runtime.task_manager.create_task(
        title=f"Update pool properties for {pool_name}",
        kind="pool.properties",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued pool property update.",
        metadata={"change_count": len(payload.changes)},
    )
    await runtime.task_manager.mark_running(task.id, message=f"Updating pool properties for {pool_name}...", progress=25)

    results = await runtime.pool_property_updater.apply_pool_changes(pool=pool_name, changes=payload.changes)

    refreshed = False
    refresh_error: str | None = None
    try:
        # Force a fresh SSH read so the UI sees the real post-write state.
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    response = PoolPropertyUpdateResponse(
        pool=pool_name,
        task_id=task.id,
        results=results,
        refreshed=refreshed,
        refresh_error=refresh_error,
    )
    await runtime.task_manager.mark_finished(
        task.id,
        success=all(item.success for item in results) if results else False,
        message=build_multi_result_task_message(
            success_count=sum(1 for item in results if item.success),
            total_count=len(results),
            refresh_error=refresh_error,
            noun="pool properties",
        ),
        command_logs=[task_log_from_multi_result(item.property, item) for item in results],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return response


@router.post("/pools/{pool_name}/scrub/start", response_model=PoolScrubResponse, tags=["pools"])
async def start_pool_scrub(pool_name: str) -> PoolScrubResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool scrub requires SSH mode.")

    state = await state_store.get_state()
    pool = require_pool(pool_name=pool_name, state=state)
    if pool_has_active_scrub(pool):
        raise HTTPException(status_code=400, detail=f"Pool {pool_name!r} already has an active scrub.")

    task = await runtime.task_manager.create_task(
        title=f"Start scrub for pool {pool_name}",
        kind="pool.scrub.start",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued scrub start.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Starting scrub for pool {pool_name}...", progress=15, stage="scrub-starting")

    result = await runtime.pool_scrubber.start_scrub(pool_name)

    refreshed = False
    refresh_error: str | None = None
    refreshed_state = state
    try:
        refreshed_state = await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    finalized = result.model_copy(update={"task_id": task.id, "refreshed": refreshed, "refresh_error": refresh_error})
    if not result.success:
        await runtime.task_manager.mark_finished(
            task.id,
            success=False,
            message=build_single_result_task_message(
                success=False,
                success_text=f"Scrub start submitted for pool {pool_name}.",
                failure_text=result.message,
                refresh_error=refresh_error,
            ),
            progress=100,
            stage="failed",
            command_logs=[task_log_from_single_result(label=pool_name, result=result)],
            metadata={"refreshed": refreshed, "refresh_error": refresh_error},
        )
    else:
        # Scrub is a long-running pool-side operation, so after the command
        # succeeds we immediately hand control back to the recovery layer.
        await runtime.task_recovery_service.reconcile_active_tasks(refreshed_state)
        await runtime.task_manager.update_task(
            task.id,
            message=(result.message if not refresh_error else f"{result.message} State refresh warning: {refresh_error}"),
            metadata={
                "refreshed": refreshed,
                "refresh_error": refresh_error,
                "command": result.command,
                "exit_status": result.exit_status,
            },
            command_logs=[task_log_from_single_result(label=pool_name, result=result)],
        )
    return finalized


@router.post("/pools/{pool_name}/scrub/stop", response_model=PoolScrubResponse, tags=["pools"])
async def stop_pool_scrub(pool_name: str) -> PoolScrubResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool scrub stop requires SSH mode.")

    state = await state_store.get_state()
    pool = require_pool(pool_name=pool_name, state=state)
    if not pool_has_active_scrub(pool):
        raise HTTPException(status_code=400, detail=f"Pool {pool_name!r} does not have an active scrub.")

    task = await runtime.task_manager.create_task(
        title=f"Stop scrub for pool {pool_name}",
        kind="pool.scrub.stop",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued scrub stop.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Stopping scrub for pool {pool_name}...", progress=20, stage="scrub-stopping")

    result = await runtime.pool_scrubber.stop_scrub(pool_name)

    refreshed = False
    refresh_error: str | None = None
    refreshed_state = state
    try:
        refreshed_state = await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    finalized = result.model_copy(update={"task_id": task.id, "refreshed": refreshed, "refresh_error": refresh_error})
    if not result.success:
        await runtime.task_manager.mark_finished(
            task.id,
            success=False,
            message=build_single_result_task_message(
                success=False,
                success_text=f"Scrub stop submitted for pool {pool_name}.",
                failure_text=result.message,
                refresh_error=refresh_error,
            ),
            progress=100,
            stage="failed",
            command_logs=[task_log_from_single_result(label=pool_name, result=result)],
            metadata={"refreshed": refreshed, "refresh_error": refresh_error},
        )
    else:
        await runtime.task_recovery_service.reconcile_active_tasks(refreshed_state)
        await runtime.task_manager.update_task(
            task.id,
            message=(result.message if not refresh_error else f"{result.message} State refresh warning: {refresh_error}"),
            metadata={
                "refreshed": refreshed,
                "refresh_error": refresh_error,
                "command": result.command,
                "exit_status": result.exit_status,
            },
            command_logs=[task_log_from_single_result(label=pool_name, result=result)],
        )
    return finalized


@router.post("/pools/{pool_name}/topology", response_model=PoolTopologyUpdateResponse, tags=["pools"])
async def update_pool_topology(
    pool_name: str,
    payload: PoolTopologyUpdateRequest,
) -> PoolTopologyUpdateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Pool topology updates require SSH mode.")

    if not payload.additions:
        raise HTTPException(status_code=400, detail="No topology additions were provided.")

    state = await state_store.get_state()
    validate_topology_additions(pool_name=pool_name, payload=payload, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Update pool topology for {pool_name}",
        kind="pool.topology",
        scope_type="pool",
        scope_name=pool_name,
        message="Queued pool topology update.",
        metadata={"addition_count": len(payload.additions)},
    )
    await runtime.task_manager.mark_running(task.id, message=f"Updating pool topology for {pool_name}...", progress=25)

    results = await runtime.pool_topology_updater.apply_pool_additions(
        pool=pool_name,
        additions=payload.additions,
        force=payload.force,
    )

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    response = PoolTopologyUpdateResponse(
        pool=pool_name,
        task_id=task.id,
        results=results,
        refreshed=refreshed,
        refresh_error=refresh_error,
    )
    await runtime.task_manager.mark_finished(
        task.id,
        success=all(item.success for item in results) if results else False,
        message=build_multi_result_task_message(
            success_count=sum(1 for item in results if item.success),
            total_count=len(results),
            refresh_error=refresh_error,
            noun="topology additions",
        ),
        command_logs=[task_log_from_multi_result(item.category, item) for item in results],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return response
