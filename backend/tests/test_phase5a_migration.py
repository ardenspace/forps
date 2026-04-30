"""Phase 5a 마이그레이션 회귀 — GitPushEvent.before_commit_sha 컬럼."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.project import Project
from app.models.workspace import Workspace


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def test_existing_events_have_null_before_sha(async_session: AsyncSession):
    """기존 GitPushEvent 데이터는 NULL 보존."""
    proj = await _seed_project(async_session)
    event = GitPushEvent(
        project_id=proj.id,
        branch="main",
        head_commit_sha="a" * 40,
        commits=[],
        commits_truncated=False,
        pusher="alice",
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)
    assert event.before_commit_sha is None


async def test_before_sha_accepts_40_char_hex(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    event = GitPushEvent(
        project_id=proj.id,
        branch="main",
        head_commit_sha="a" * 40,
        before_commit_sha="b" * 40,
        commits=[],
        commits_truncated=False,
        pusher="alice",
    )
    async_session.add(event)
    await async_session.commit()
    await async_session.refresh(event)
    assert event.before_commit_sha == "b" * 40


async def test_before_sha_check_rejects_invalid_hex(async_session: AsyncSession):
    """CHECK 제약 — non-hex 또는 길이 != 40 reject."""
    proj = await _seed_project(async_session)
    event = GitPushEvent(
        project_id=proj.id,
        branch="main",
        head_commit_sha="a" * 40,
        before_commit_sha="not-hex-shasha",
        commits=[],
        commits_truncated=False,
        pusher="alice",
    )
    async_session.add(event)
    with pytest.raises(IntegrityError):
        await async_session.commit()


async def test_migration_added_column_to_git_push_events_table(async_session: AsyncSession):
    result = await async_session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'git_push_events' AND column_name = 'before_commit_sha'"
        )
    )
    row = result.first()
    assert row is not None
    assert row[0] == "before_commit_sha"
