from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from app import runtime
from app.core.auth import require_authenticated_request
from app.core.state import state_store
from app.schemas.task import TaskDetailResponse, TaskListResponse
from app.schemas.task_schedule import (
    TaskScheduleCreateRequest,
    TaskScheduleDetailResponse,
    TaskScheduleListResponse,
    TaskScheduleUpdateRequest,
)
from app.api.validators import validate_task_schedule_payload, validate_task_schedule_update

router = APIRouter(prefix="/api")


@router.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
async def list_tasks(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None),
) -> TaskListResponse:
    require_authenticated_request(request)
    await runtime.task_recovery_service.reconcile_active_tasks(await state_store.get_state())
    (
        tasks,
        total,
        filtered_total,
        normalized_page,
        normalized_page_size,
        total_pages,
        running_count,
        completed_count,
        failed_count,
    ) = await runtime.task_manager.list_tasks(page=page, page_size=page_size, status_filter=status_filter)
    return TaskListResponse(
        tasks=tasks,
        total=total,
        filtered_total=filtered_total,
        page=normalized_page,
        page_size=normalized_page_size,
        total_pages=total_pages,
        running_count=running_count,
        completed_count=completed_count,
        failed_count=failed_count,
    )


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse, tags=["tasks"])
async def get_task(task_id: str, request: Request) -> TaskDetailResponse:
    require_authenticated_request(request)
    await runtime.task_recovery_service.reconcile_active_tasks(await state_store.get_state())
    task = await runtime.task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} was not found.")
    return TaskDetailResponse(task=task)


@router.get("/task-schedules", response_model=TaskScheduleListResponse, tags=["tasks"])
async def list_task_schedules(request: Request) -> TaskScheduleListResponse:
    require_authenticated_request(request)
    return TaskScheduleListResponse(schedules=await runtime.task_scheduler.list_schedules())


@router.post("/task-schedules", response_model=TaskScheduleDetailResponse, tags=["tasks"])
async def create_task_schedule(
    payload: TaskScheduleCreateRequest,
    request: Request,
) -> TaskScheduleDetailResponse:
    require_authenticated_request(request)
    await validate_task_schedule_payload(payload)
    schedule = await runtime.task_scheduler.create_schedule(payload)
    return TaskScheduleDetailResponse(schedule=schedule)


@router.patch("/task-schedules/{schedule_id}", response_model=TaskScheduleDetailResponse, tags=["tasks"])
async def update_task_schedule(
    schedule_id: str,
    payload: TaskScheduleUpdateRequest,
    request: Request,
) -> TaskScheduleDetailResponse:
    require_authenticated_request(request)
    existing = await runtime.task_scheduler.get_schedule(schedule_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Task schedule {schedule_id!r} was not found.")
    await validate_task_schedule_update(existing.kind, existing.scope_type, existing.scope_name, existing.schedule_type, payload)
    schedule = await runtime.task_scheduler.update_schedule(schedule_id, payload)
    if schedule is None:
        raise HTTPException(status_code=404, detail=f"Task schedule {schedule_id!r} was not found.")
    return TaskScheduleDetailResponse(schedule=schedule)


@router.delete("/task-schedules/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
async def delete_task_schedule(schedule_id: str, request: Request) -> Response:
    require_authenticated_request(request)
    deleted = await runtime.task_scheduler.delete_schedule(schedule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task schedule {schedule_id!r} was not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
