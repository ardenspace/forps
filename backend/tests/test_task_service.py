"""task_service handoff_missing annotation 회귀.

설계서: 2026-05-01-phase-5-followup-b2-design.md §2.1
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.handoff import Handoff
from app.models.project import Project
from app.models.task import Task, TaskSource, TaskStatus
from app.models.workspace import Workspace
from app.services import task_service


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def _seed_task(
    db: AsyncSession, project: Project, *,
    source: TaskSource = TaskSource.MANUAL,
    last_commit_sha: str | None = None,
    archived_at: datetime | None = None,
    external_id: str | None = None,
) -> Task:
    t = Task(
        project_id=project.id,
        title="t",
        status=TaskStatus.TODO,
        source=source,
        last_commit_sha=last_commit_sha,
        archived_at=archived_at,
        external_id=external_id,
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


async def _seed_handoff(db: AsyncSession, project: Project, *, commit_sha: str) -> Handoff:
    h = Handoff(
        project_id=project.id,
        branch="main",
        author_git_login="alice",
        commit_sha=commit_sha,
        pushed_at=datetime.utcnow(),
        parsed_tasks=[],
        free_notes={},
        raw_content="x",
    )
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h


async def test_handoff_missing_true_when_synced_task_has_no_handoff(
    async_session: AsyncSession,
):
    """SYNCED + last_commit_sha set + handoff 없음 → handoff_missing = true."""
    proj = await _seed_project(async_session)
    await _seed_task(
        async_session, proj,
        source=TaskSource.SYNCED_FROM_PLAN,
        last_commit_sha="a" * 40,
        external_id="task-001",
    )

    tasks = await task_service.get_project_tasks(
        async_session, proj.id, uuid.uuid4(), filters=None,
    )
    assert len(tasks) == 1
    assert tasks[0].handoff_missing is True


async def test_handoff_missing_false_when_handoff_exists(
    async_session: AsyncSession,
):
    """SYNCED + last_commit_sha set + handoff 존재 → handoff_missing = false."""
    proj = await _seed_project(async_session)
    sha = "b" * 40
    await _seed_task(
        async_session, proj,
        source=TaskSource.SYNCED_FROM_PLAN,
        last_commit_sha=sha,
        external_id="task-002",
    )
    await _seed_handoff(async_session, proj, commit_sha=sha)

    tasks = await task_service.get_project_tasks(
        async_session, proj.id, uuid.uuid4(), filters=None,
    )
    assert len(tasks) == 1
    assert tasks[0].handoff_missing is False


async def test_handoff_missing_false_for_excluded_cases(
    async_session: AsyncSession,
):
    """MANUAL / last_commit_sha NULL / archived task 는 항상 handoff_missing = false."""
    proj = await _seed_project(async_session)
    # case 1: MANUAL task with last_commit_sha set
    await _seed_task(
        async_session, proj,
        source=TaskSource.MANUAL,
        last_commit_sha="c" * 40,
    )
    # case 2: SYNCED 인데 last_commit_sha NULL
    await _seed_task(
        async_session, proj,
        source=TaskSource.SYNCED_FROM_PLAN,
        last_commit_sha=None,
        external_id="task-003",
    )
    # case 3: SYNCED 인데 archived
    await _seed_task(
        async_session, proj,
        source=TaskSource.SYNCED_FROM_PLAN,
        last_commit_sha="d" * 40,
        archived_at=datetime.utcnow(),
        external_id="task-004",
    )

    tasks = await task_service.get_project_tasks(
        async_session, proj.id, uuid.uuid4(), filters=None,
    )
    assert len(tasks) == 3
    for t in tasks:
        assert t.handoff_missing is False, f"task {t.title} should have handoff_missing=False"
