"""sync_service — webhook 이벤트 → DB 반영 통합 테스트.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (⑤), §7.1, §10.2
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.handoff import Handoff
from app.models.project import Project
from app.models.task import Task, TaskSource, TaskStatus
from app.models.task_event import TaskEvent, TaskEventAction
from app.models.workspace import Workspace
from app.services.sync_service import process_event


async def _seed_project(
    db: AsyncSession, *, repo_url: str | None = "https://github.com/ardenspace/app-chak"
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p", git_repo_url=repo_url)
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def _seed_event(
    db: AsyncSession,
    project: Project,
    *,
    head_sha: str = "a" * 40,
    branch: str = "main",
    commits: list[dict] | None = None,
    commits_truncated: bool = False,
    processed_at: datetime | None = None,
) -> GitPushEvent:
    event = GitPushEvent(
        project_id=project.id,
        branch=branch,
        head_commit_sha=head_sha,
        commits=commits or [],
        commits_truncated=commits_truncated,
        pusher="alice",
        processed_at=processed_at,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def _noop_fetch_file(repo_url: str, pat: str | None, sha: str, path: str) -> str | None:
    return None


async def _noop_fetch_compare(repo_url: str, pat: str | None, base: str, head: str) -> list[str]:
    return []


async def test_process_event_skips_already_processed(async_session: AsyncSession):
    """processed_at IS NOT NULL 이면 즉시 종료 — DB 변경 없음."""
    proj = await _seed_project(async_session)
    event = await _seed_event(
        async_session, proj, processed_at=datetime.utcnow() - timedelta(minutes=10)
    )
    initial_processed_at = event.processed_at

    await process_event(
        async_session, event,
        fetch_file=_noop_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at == initial_processed_at
    assert event.error is None


async def test_process_event_marks_processed_when_no_relevant_files(
    async_session: AsyncSession,
):
    """변경 파일 중 PLAN/handoff 없음 → fetch 안 함, processed_at = now()."""
    proj = await _seed_project(async_session)
    event = await _seed_event(
        async_session, proj,
        commits=[{"modified": ["frontend/Button.tsx"], "added": [], "removed": []}],
    )

    await process_event(
        async_session, event,
        fetch_file=_noop_fetch_file, fetch_compare=_noop_fetch_compare,
    )

    await async_session.refresh(event)
    assert event.processed_at is not None
    assert event.error is None
