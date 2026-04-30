"""Task 모델 4 필드 확장 검증 (모델만, alembic 은 Task 11)."""
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskSource


def test_task_has_new_fields():
    annotations = Task.__annotations__
    assert "source" in annotations
    assert "external_id" in annotations
    assert "last_commit_sha" in annotations
    assert "archived_at" in annotations


def test_task_source_default_manual():
    """기존 데이터 호환: 새 컬럼 default = MANUAL."""
    t = Task(project_id=None, title="x")  # type: ignore[arg-type]
    assert t.source == TaskSource.MANUAL
    assert t.external_id is None
    assert t.last_commit_sha is None
    assert t.archived_at is None


async def test_task_response_exposes_phase1_fields(async_session: AsyncSession):
    """Phase 5b: TaskResponse 가 source / external_id / last_commit_sha / archived_at 노출."""
    import uuid

    from app.models.project import Project
    from app.models.task import Task, TaskSource
    from app.models.workspace import Workspace
    from app.schemas.task import TaskResponse

    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.flush()
    task = Task(
        project_id=proj.id,
        title="t",
        source=TaskSource.SYNCED_FROM_PLAN,
        external_id="task-001",
        last_commit_sha="a" * 40,
    )
    async_session.add(task)
    await async_session.commit()
    await async_session.refresh(task)

    response = TaskResponse.model_validate(task)
    assert response.source == TaskSource.SYNCED_FROM_PLAN
    assert response.external_id == "task-001"
    assert response.last_commit_sha == "a" * 40
    assert response.archived_at is None
