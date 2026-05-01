"""log_fingerprint_reaper 단위 테스트.

설계서: 2026-05-01-error-log-phase3-design.md §2.7, §3.6
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.error_group import ErrorGroup
from app.models.log_event import LogEvent, LogLevel
from app.models.project import Project
from app.models.workspace import Workspace
from app.services import log_fingerprint_reaper


@pytest.fixture(autouse=True)
def _patch_reaper_session(upgraded_db, monkeypatch):
    """run_reaper_once() 가 테스트 DB 에 접속하도록 AsyncSessionLocal 교체.

    AsyncSessionLocal 은 모듈 임포트 시 placeholder URL 로 바인딩되므로,
    각 테스트마다 per-test 컨테이너 DB 를 가리키는 sessionmaker 로 교체한다.
    """
    engine = create_async_engine(upgraded_db["async_url"], echo=False)
    test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(log_fingerprint_reaper, "AsyncSessionLocal", test_session_factory)
    yield
    import asyncio
    asyncio.get_event_loop().run_until_complete(engine.dispose())


async def _seed_unfingerprinted_events(
    async_session: AsyncSession, *, count: int, level: LogLevel,
) -> Project:
    ws = Workspace(name="ws", slug=f"ws-{uuid.uuid4().hex[:8]}")
    async_session.add(ws)
    await async_session.flush()
    proj = Project(workspace_id=ws.id, name="p")
    async_session.add(proj)
    await async_session.flush()
    for i in range(count):
        async_session.add(LogEvent(
            project_id=proj.id, level=level,
            message=f"boom-{i}", logger_name="app.x", version_sha="a" * 40,
            environment="production", hostname="h",
            emitted_at=datetime.utcnow(), received_at=datetime.utcnow(),
            # 같은 exception_class + exception_message → 동일 fingerprint (fallback: no stack_frames)
            exception_class="KeyError", exception_message="'key'",
            fingerprint=None, fingerprinted_at=None,
        ))
    await async_session.commit()
    await async_session.refresh(proj)
    return proj


async def test_reaper_processes_unfingerprinted_errors(async_session: AsyncSession):
    """ERROR↑ unfingerprinted → fingerprint + group + 마킹."""
    proj = await _seed_unfingerprinted_events(async_session, count=3, level=LogLevel.ERROR)

    await log_fingerprint_reaper.run_reaper_once()

    rows = (await async_session.execute(
        select(LogEvent).where(LogEvent.project_id == proj.id)
    )).scalars().all()
    assert all(e.fingerprint is not None for e in rows)
    assert all(e.fingerprinted_at is not None for e in rows)

    # 같은 fingerprint (같은 logger / class / no stack_frames → fallback) — 1 group
    groups = (await async_session.execute(
        select(ErrorGroup).where(ErrorGroup.project_id == proj.id)
    )).scalars().all()
    assert len(groups) == 1
    assert groups[0].event_count == 3


async def test_reaper_skips_info_level(async_session: AsyncSession):
    """INFO/WARNING level 은 회수 안 함 (filter)."""
    proj = await _seed_unfingerprinted_events(async_session, count=2, level=LogLevel.WARNING)

    await log_fingerprint_reaper.run_reaper_once()

    rows = (await async_session.execute(
        select(LogEvent).where(LogEvent.project_id == proj.id)
    )).scalars().all()
    # 회수 안 함 — fingerprint 그대로 NULL
    assert all(e.fingerprint is None for e in rows)
    assert all(e.fingerprinted_at is None for e in rows)


async def test_reaper_chunked_processes_large_backlog(
    async_session: AsyncSession, monkeypatch: pytest.MonkeyPatch,
):
    """200건 backlog → 100/batch 로 2 batch 처리."""
    proj = await _seed_unfingerprinted_events(async_session, count=200, level=LogLevel.ERROR)

    monkeypatch.setattr(log_fingerprint_reaper, "REAPER_BATCH_SIZE", 100)

    await log_fingerprint_reaper.run_reaper_once()

    rows = (await async_session.execute(
        select(LogEvent).where(LogEvent.project_id == proj.id)
    )).scalars().all()
    assert all(e.fingerprinted_at is not None for e in rows)
