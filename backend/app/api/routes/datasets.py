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
    require_dataset,
    validate_dataset_creation,
    validate_dataset_destroy,
    validate_dataset_property_changes,
)
from app.core.state import state_store
from app.schemas.dataset_create import DatasetCreateRequest, DatasetCreateResponse
from app.schemas.dataset_destroy import DatasetDestroyResponse
from app.schemas.dataset_property_update import DatasetPropertyUpdateRequest, DatasetPropertyUpdateResponse

router = APIRouter(prefix="/api")


@router.post("/datasets", response_model=DatasetCreateResponse, tags=["datasets"])
async def create_dataset(payload: DatasetCreateRequest) -> DatasetCreateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset creation requires SSH mode.")

    state = await state_store.get_state()
    validate_dataset_creation(payload=payload, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Create dataset {payload.full_name}",
        kind="dataset.create",
        scope_type="dataset",
        scope_name=payload.full_name,
        message="Queued dataset creation.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Creating dataset {payload.full_name}...", progress=25)

    result = await runtime.dataset_creator.create_dataset(payload)

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
            success_text=f"Dataset {payload.full_name} created.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=payload.full_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/datasets/{dataset_name:path}/destroy", response_model=DatasetDestroyResponse, tags=["datasets"])
async def destroy_dataset(dataset_name: str) -> DatasetDestroyResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset destroy requires SSH mode.")

    state = await state_store.get_state()
    dataset = require_dataset(dataset_name=dataset_name, state=state)
    validate_dataset_destroy(dataset=dataset)

    task = await runtime.task_manager.create_task(
        title=f"Destroy dataset {dataset_name}",
        kind="dataset.destroy",
        scope_type="dataset",
        scope_name=dataset_name,
        message="Queued dataset destroy.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Destroying dataset {dataset_name}...", progress=25)

    result = await runtime.dataset_destroyer.destroy_dataset(dataset_name)

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
            success_text=f"Dataset {dataset_name} destroyed.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=dataset_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/datasets/{dataset_name:path}/properties", response_model=DatasetPropertyUpdateResponse, tags=["datasets"])
async def update_dataset_properties(
    dataset_name: str,
    payload: DatasetPropertyUpdateRequest,
) -> DatasetPropertyUpdateResponse:
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Dataset property updates require SSH mode.")

    if not payload.changes:
        raise HTTPException(status_code=400, detail="No property changes were provided.")

    state = await state_store.get_state()
    dataset = require_dataset(dataset_name=dataset_name, state=state)
    validate_dataset_property_changes(dataset=dataset, payload=payload)

    task = await runtime.task_manager.create_task(
        title=f"Update dataset properties for {dataset_name}",
        kind="dataset.properties",
        scope_type="dataset",
        scope_name=dataset_name,
        message="Queued dataset property update.",
        metadata={"change_count": len(payload.changes)},
    )
    await runtime.task_manager.mark_running(task.id, message=f"Updating dataset properties for {dataset_name}...", progress=25)

    results = await runtime.dataset_property_updater.apply_dataset_changes(dataset=dataset_name, changes=payload.changes)

    refreshed = False
    refresh_error: str | None = None
    try:
        await runtime.poller.refresh_once(force_all=True)
        refreshed = True
    except Exception as exc:
        refresh_error = str(exc)

    response = DatasetPropertyUpdateResponse(
        dataset=dataset_name,
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
            noun="dataset properties",
        ),
        command_logs=[task_log_from_multi_result(item.property, item) for item in results],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return response
