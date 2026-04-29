"""push_event_reaper — 부팅 시 미처리 GitPushEvent 회수.

설계서: 2026-04-26-ai-task-automation-design.md §5.1 (⑧), §7.1, §10.4
- `processed_at IS NULL AND received_at < now() - 5min` 인 이벤트 재처리
- Phase 2: process callback이 None이면 logging only (sync 로직은 Phase 4)
"""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.git_push_event import GitPushEvent
from app.models.project import Project
from app.models.workspace import Workspace
from app.services.push_event_reaper import REAPER_GRACE, reap_pending_events


async def _seed_project(db: AsyncSession) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    db.add(ws)
    await db.flush()
    proj = Project(workspace_id=ws.id, name="p")
    db.add(proj)
    await db.commit()
    await db.refresh(proj)
    return proj


async def _seed_event(
    db: AsyncSession,
    project: Project,
    *,
    received_at: datetime,
    processed_at: datetime | None = None,
    head_sha: str | None = None,
) -> GitPushEvent:
    event = GitPushEvent(
        project_id=project.id,
        branch="main",
        head_commit_sha=head_sha or ("a" * 40),
        commits=[],
        commits_truncated=False,
        pusher="alice",
        received_at=received_at,
        processed_at=processed_at,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def test_reaper_finds_old_unprocessed_events(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    old = await _seed_event(
        async_session,
        proj,
        received_at=datetime.utcnow() - timedelta(minutes=10),
        head_sha="a" * 40,
    )
    # 5분 미만 — 처리 중일 수 있음, skip
    fresh = await _seed_event(
        async_session,
        proj,
        received_at=datetime.utcnow() - timedelta(minutes=2),
        head_sha="b" * 40,
    )

    found_ids: list[uuid.UUID] = []

    async def callback(event: GitPushEvent) -> None:
        found_ids.append(event.id)

    count = await reap_pending_events(async_session, callback)
    assert count == 1
    assert found_ids == [old.id]


async def test_reaper_skips_processed_events(async_session: AsyncSession):
    proj = await _seed_project(async_session)
    await _seed_event(
        async_session,
        proj,
        received_at=datetime.utcnow() - timedelta(hours=1),
        processed_at=datetime.utcnow() - timedelta(minutes=30),
        head_sha="c" * 40,
    )

    callback_invocations = 0

    async def callback(event: GitPushEvent) -> None:
        nonlocal callback_invocations
        callback_invocations += 1

    count = await reap_pending_events(async_session, callback)
    assert count == 0
    assert callback_invocations == 0


async def test_reaper_with_no_callback_just_logs(
    async_session: AsyncSession, caplog: pytest.LogCaptureFixture
):
    """Phase 2: callback=None 이면 logging만 — Phase 4 에서 sync_service.process_event 주입."""
    import logging

    proj = await _seed_project(async_session)
    await _seed_event(
        async_session,
        proj,
        received_at=datetime.utcnow() - timedelta(minutes=15),
        head_sha="d" * 40,
    )

    with caplog.at_level(logging.INFO, logger="app.services.push_event_reaper"):
        count = await reap_pending_events(async_session, None)

    assert count == 1
    assert any("pending push event" in rec.message for rec in caplog.records)


async def test_reaper_grace_constant_is_5_minutes():
    assert REAPER_GRACE == timedelta(minutes=5)
