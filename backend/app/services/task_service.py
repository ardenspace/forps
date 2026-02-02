from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task
from app.models.task_event import TaskEvent, TaskEventAction
from app.schemas.task import TaskCreate, TaskUpdate


def _task_query():
    return select(Task).options(
        selectinload(Task.assignee),
        selectinload(Task.reporter),
    )


async def get_week_tasks(db: AsyncSession, user_id: UUID, week_start: date) -> list[Task]:
    week_end = week_start + timedelta(days=7)
    result = await db.execute(
        _task_query()
        .where(Task.assignee_id == user_id)
        .where(Task.due_date >= week_start)
        .where(Task.due_date < week_end)
        .order_by(Task.due_date)
    )
    return list(result.scalars().all())


async def get_task(db: AsyncSession, task_id: UUID) -> Task | None:
    result = await db.execute(_task_query().where(Task.id == task_id))
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, project_id: UUID, user_id: UUID, data: TaskCreate) -> Task:
    task = Task(
        project_id=project_id,
        reporter_id=user_id,
        **data.model_dump(),
    )
    db.add(task)
    await db.flush()

    db.add(TaskEvent(task_id=task.id, user_id=user_id, action=TaskEventAction.CREATED))
    await db.commit()
    await db.refresh(task)

    # reload with relationships
    return await get_task(db, task.id)  # type: ignore[return-value]


async def update_task(db: AsyncSession, task_id: UUID, user_id: UUID, data: TaskUpdate) -> Task | None:
    task = await get_task(db, task_id)
    if not task:
        return None

    changes: dict = {}
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old = getattr(task, field)
        if old != value:
            changes[field] = {"old": str(old), "new": str(value)}
            setattr(task, field, value)

    if changes:
        action = TaskEventAction.STATUS_CHANGED if "status" in changes else TaskEventAction.UPDATED
        db.add(TaskEvent(task_id=task_id, user_id=user_id, action=action, changes=changes))

    await db.commit()
    return await get_task(db, task_id)


async def delete_task(db: AsyncSession, task_id: UUID) -> bool:
    task = await get_task(db, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True


