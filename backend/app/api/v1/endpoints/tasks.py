from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import CurrentUser
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskFilters,
)
from app.services import task_service
from app.services.permission_service import get_effective_role, can_edit, can_manage

router = APIRouter(tags=["tasks"])


# ── Project Tasks (중첩 리소스) ────────────────────────────

@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_project_tasks(
    project_id: UUID,
    status: TaskStatus | None = None,
    assignee_id: UUID | None = None,
    mine_only: bool = False,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """프로젝트의 태스크 목록 (Board용)"""
    role = await get_effective_role(db, user.id, project_id)
    if not role:
        raise HTTPException(status_code=403, detail="Permission denied")

    filters = TaskFilters(status=status, assignee_id=assignee_id, mine_only=mine_only)
    return await task_service.get_project_tasks(db, project_id, user.id, filters)


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """태스크 생성 (editor 이상)"""
    role = await get_effective_role(db, user.id, project_id)
    if not can_edit(role):
        raise HTTPException(status_code=403, detail="Permission denied")

    return await task_service.create_task(db, project_id, user.id, data)


# ── Single Task ────────────────────────────────────────────

@router.get("/tasks/week", response_model=list[TaskResponse])
async def get_week_tasks(
    week_start: date = Query(...),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """주간 태스크 조회"""
    return await task_service.get_week_tasks(db, user.id, week_start)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """태스크 상세"""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """태스크 수정 (editor 이상)"""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    role = await get_effective_role(db, user.id, task.project_id)
    if not can_edit(role):
        raise HTTPException(status_code=403, detail="Permission denied")

    return await task_service.update_task(db, task_id, user.id, data)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(),
):
    """태스크 삭제 (Owner만)"""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    role = await get_effective_role(db, user.id, task.project_id)
    if not can_manage(role):
        raise HTTPException(status_code=403, detail="Only owner can delete tasks")

    await task_service.delete_task(db, task_id, user.id)


