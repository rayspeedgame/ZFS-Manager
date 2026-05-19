from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app import runtime
from app.api.common import build_single_result_task_message, task_log_from_single_result
from app.api.validators import (
    require_dataset,
    require_snapshot,
    validate_snapshot_destroy,
    validate_snapshot_parent,
    validate_snapshot_rollback,
)
from app.core.auth import require_authenticated_request
from app.core.state import state_store
from app.schemas.snapshot import (
    DatasetSnapshotsResponse,
    SnapshotCreateRequest,
    SnapshotCreateResponse,
    SnapshotDestroyResponse,
    SnapshotDetailResponse,
    SnapshotFiltersResponse,
    SnapshotListResponse,
    SnapshotRollbackRequest,
    SnapshotRollbackResponse,
)
from app.services.snapshot_query import get_snapshot, list_dataset_snapshots, list_snapshots, snapshot_exists, snapshot_filters

router = APIRouter(prefix="/api")


@router.get("/snapshots", response_model=SnapshotListResponse, tags=["snapshots"])
async def list_snapshot_records(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str = Query(default=""),
    pool: str = Query(default=""),
    dataset: str = Query(default=""),
    snapshot_type: str = Query(default=""),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
) -> SnapshotListResponse:
    require_authenticated_request(request)
    state = await state_store.get_state()
    items, total, normalized_page, normalized_page_size, total_pages = list_snapshots(
        state,
        page=page,
        page_size=page_size,
        search=search,
        pool=pool,
        dataset=dataset,
        snapshot_type=snapshot_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return SnapshotListResponse(
        items=items,
        total=total,
        page=normalized_page,
        page_size=normalized_page_size,
        total_pages=total_pages,
    )


@router.get("/snapshots/filters", response_model=SnapshotFiltersResponse, tags=["snapshots"])
async def list_snapshot_filter_values(request: Request) -> SnapshotFiltersResponse:
    require_authenticated_request(request)
    state = await state_store.get_state()
    pools, datasets, types = snapshot_filters(state)
    return SnapshotFiltersResponse(pools=pools, datasets=datasets, types=types)


@router.get("/snapshots/{snapshot_name:path}", response_model=SnapshotDetailResponse, tags=["snapshots"])
async def get_snapshot_record(snapshot_name: str, request: Request) -> SnapshotDetailResponse:
    require_authenticated_request(request)
    state = await state_store.get_state()
    snapshot = get_snapshot(state, snapshot_name)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_name!r} was not found in the latest snapshot.")
    return SnapshotDetailResponse(snapshot=snapshot)


@router.get("/datasets/{dataset_name:path}/snapshots", response_model=DatasetSnapshotsResponse, tags=["snapshots"])
async def get_dataset_snapshots(
    dataset_name: str,
    request: Request,
    limit: int = Query(default=5, ge=1, le=50),
) -> DatasetSnapshotsResponse:
    require_authenticated_request(request)
    state = await state_store.get_state()
    dataset = require_dataset(dataset_name=dataset_name, state=state)
    validate_snapshot_parent(dataset)
    return DatasetSnapshotsResponse(snapshots=list_dataset_snapshots(state, dataset_name, limit=limit))


@router.post("/datasets/{dataset_name:path}/snapshots", response_model=SnapshotCreateResponse, tags=["snapshots"])
async def create_snapshot(dataset_name: str, payload: SnapshotCreateRequest, request: Request) -> SnapshotCreateResponse:
    require_authenticated_request(request)
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Snapshot creation requires SSH mode.")

    state = await state_store.get_state()
    dataset = require_dataset(dataset_name=dataset_name, state=state)
    validate_snapshot_parent(dataset)
    full_name = f"{dataset_name}@{payload.name}"
    if snapshot_exists(state, full_name):
        raise HTTPException(status_code=400, detail=f"Snapshot {full_name!r} already exists in the latest snapshot.")

    task = await runtime.task_manager.create_task(
        title=f"Create snapshot {full_name}",
        kind="snapshot.create",
        scope_type="snapshot",
        scope_name=full_name,
        message="Queued snapshot creation.",
        metadata={"dataset": dataset_name, "recursive": payload.recursive},
    )
    await runtime.task_manager.mark_running(task.id, message=f"Creating snapshot {full_name}...", progress=25)

    result = await runtime.snapshot_creator.create_snapshot(dataset_name, payload)

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
            success_text=f"Snapshot {full_name} created.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=full_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.delete("/snapshots/{snapshot_name:path}", response_model=SnapshotDestroyResponse, tags=["snapshots"])
async def delete_snapshot(snapshot_name: str, request: Request) -> SnapshotDestroyResponse:
    require_authenticated_request(request)
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Snapshot destroy requires SSH mode.")

    state = await state_store.get_state()
    snapshot = require_snapshot(snapshot_name=snapshot_name, state=state)
    validate_snapshot_destroy(snapshot)

    task = await runtime.task_manager.create_task(
        title=f"Delete snapshot {snapshot_name}",
        kind="snapshot.delete",
        scope_type="snapshot",
        scope_name=snapshot_name,
        message="Queued snapshot delete.",
    )
    await runtime.task_manager.mark_running(task.id, message=f"Deleting snapshot {snapshot_name}...", progress=25)

    result = await runtime.snapshot_destroyer.destroy_snapshot(snapshot_name)

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
            success_text=f"Snapshot {snapshot_name} deleted.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=snapshot_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error},
    )
    return finalized


@router.post("/snapshots/{snapshot_name:path}/rollback", response_model=SnapshotRollbackResponse, tags=["snapshots"])
async def rollback_snapshot(
    snapshot_name: str,
    payload: SnapshotRollbackRequest,
    request: Request,
) -> SnapshotRollbackResponse:
    require_authenticated_request(request)
    if runtime.config.poller.mode != "ssh":
        raise HTTPException(status_code=503, detail="Snapshot rollback requires SSH mode.")

    state = await state_store.get_state()
    snapshot = require_snapshot(snapshot_name=snapshot_name, state=state)
    validate_snapshot_rollback(snapshot=snapshot, state=state)

    task = await runtime.task_manager.create_task(
        title=f"Rollback snapshot {snapshot_name}",
        kind="snapshot.rollback",
        scope_type="snapshot",
        scope_name=snapshot_name,
        message="Queued snapshot rollback.",
        metadata={"rollback_mode": payload.mode},
    )
    await runtime.task_manager.mark_running(
        task.id,
        message=f"Rolling back snapshot {snapshot_name} with mode {payload.mode}...",
        progress=25,
    )

    result = await runtime.snapshot_rollbacker.rollback_snapshot(snapshot_name, payload.mode)

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
            success_text=f"Snapshot {snapshot_name} rolled back with mode {payload.mode}.",
            failure_text=result.message,
            refresh_error=refresh_error,
        ),
        command_logs=[task_log_from_single_result(label=snapshot_name, result=result)],
        metadata={"refreshed": refreshed, "refresh_error": refresh_error, "rollback_mode": payload.mode},
    )
    return finalized
